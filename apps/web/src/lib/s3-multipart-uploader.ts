import {
  completeMultipartUploadApi,
  initiateMultipartUploadApi,
  presignPartsApi,
} from "@/components/documents/documents-api";
import { CompletedPartItem } from "@/components/documents/types";

export interface UploadProgressCallback {
  (percentage: number, loadedBytes: number, totalBytes: number): void;
}

export async function uploadFileDirectToS3(
  workspaceId: string,
  file: File,
  onProgress?: UploadProgressCallback,
  signal?: AbortSignal,
): Promise<{ documentId: string; status: string }> {
  // Step 1: Initiate Multipart on Backend & S3
  const init = await initiateMultipartUploadApi(
    workspaceId,
    file.name,
    file.size,
    file.type || "application/octet-stream",
  );

  const { document_id: documentId, upload_id: uploadId, s3_key: s3Key, chunk_size_bytes: chunkSize, total_parts: totalParts } = init;

  // Step 2: Request Presigned URLs for all parts
  const partNumbers = Array.from({ length: totalParts }, (_, i) => i + 1);
  const { parts: presignedParts } = await presignPartsApi(documentId, uploadId, s3Key, partNumbers);

  const completedParts: CompletedPartItem[] = [];
  let uploadedBytes = 0;
  const CONCURRENCY_LIMIT = 3;

  // Step 3: Upload chunks in parallel using worker pool
  const uploadQueue = [...presignedParts];

  async function worker() {
    while (uploadQueue.length > 0) {
      if (signal?.aborted) throw new Error("Upload aborted by user");
      const part = uploadQueue.shift();
      if (!part) break;

      const start = (part.part_number - 1) * chunkSize;
      const end = Math.min(start + chunkSize, file.size);
      const chunkBlob = file.slice(start, end);

      let attempts = 0;
      let success = false;
      let etag = "";

      while (attempts < 3 && !success) {
        try {
          if (signal?.aborted) throw new Error("Upload aborted");
          const response = await fetch(part.presigned_url, {
            method: "PUT",
            body: chunkBlob,
            signal,
          });

          if (!response.ok) {
            throw new Error(`S3 returned HTTP ${response.status}`);
          }

          etag = response.headers.get("ETag") || `part-${part.part_number}`;
          success = true;
        } catch (err: unknown) {
          attempts += 1;
          if (attempts >= 3) {
            const rawMsg = err instanceof Error ? err.message : String(err);
            if (rawMsg.includes("Failed to fetch")) {
              throw new Error("S3 Upload blocked (Check S3 CORS or network)");
            }
            throw err;
          }
          await new Promise((r) => setTimeout(r, 1000 * attempts));
        }
      }

      completedParts.push({ part_number: part.part_number, etag });
      uploadedBytes += (end - start);

      if (onProgress) {
        const percent = Math.min(99, Math.round((uploadedBytes / file.size) * 100));
        onProgress(percent, uploadedBytes, file.size);
      }
    }
  }

  const workers = Array.from({ length: Math.min(CONCURRENCY_LIMIT, totalParts) }, () => worker());
  await Promise.all(workers);

  // Step 4: Complete Multipart Upload on S3 & Register Ingestion Job
  const completeRes = await completeMultipartUploadApi(documentId, uploadId, s3Key, completedParts);

  if (onProgress) {
    onProgress(100, file.size, file.size);
  }

  return { documentId, status: completeRes.status };
}
