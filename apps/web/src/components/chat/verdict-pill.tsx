import React from "react";
import { Badge } from "@/components/ui/badge";
import { Verdict } from "@/types";

export interface VerdictPillProps {
  verdict: Verdict;
}

export const VerdictPill: React.FC<VerdictPillProps> = ({ verdict }) => {
  if (verdict === "answered") {
    return <Badge variant="success">Answered</Badge>;
  }
  if (verdict === "insufficient_evidence") {
    return <Badge variant="danger">Insufficient Evidence</Badge>;
  }
  if (verdict === "unverified") {
    return <Badge variant="warning">Unverified Citations</Badge>;
  }
  return <Badge variant="neutral">System Error</Badge>;
};
