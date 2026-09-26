import React, { useState } from "react";
import { UserPlus, Trash2 } from "lucide-react";
import { ProjectMember, Role } from "@/types";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export interface MembersTableProps {
  members: ProjectMember[];
  onAddMember: (email: string, role: Role) => Promise<void>;
  onRemoveMember: (userId: string) => Promise<void>;
}

export const MembersTable: React.FC<MembersTableProps> = ({
  members,
  onAddMember,
  onRemoveMember,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("viewer");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setIsSubmitting(true);
    try {
      await onAddMember(email.trim(), role);
      setEmail("");
      setIsOpen(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-semibold text-slate-800">Project Members</h3>
        <Button size="sm" onClick={() => setIsOpen(true)}>
          <UserPlus className="h-4 w-4 mr-1.5" />
          Invite Member
        </Button>
      </div>

      <div className="border border-slate-200 rounded-xl bg-white overflow-hidden shadow-sm">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500">
              <th className="p-3">User</th>
              <th className="p-3">Email</th>
              <th className="p-3">Role</th>
              <th className="p-3">Joined At</th>
              <th className="p-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {members.map((m) => (
              <tr key={m.user.id} className="hover:bg-slate-50">
                <td className="p-3 font-medium text-slate-900">{m.user.full_name || "User"}</td>
                <td className="p-3 text-slate-600">{m.user.email}</td>
                <td className="p-3">
                  <Badge variant={m.role === "owner" ? "default" : "neutral"}>
                    {m.role}
                  </Badge>
                </td>
                <td className="p-3 text-slate-500">{new Date(m.joined_at).toLocaleDateString()}</td>
                <td className="p-3 text-right">
                  {m.role !== "owner" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onRemoveMember(m.user.id)}
                      className="text-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title="Invite Project Member">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="colleague@organization.com"
            required
          />
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
            >
              <option value="viewer">Viewer (Read & Chat only)</option>
              <option value="editor">Editor (Upload, Chat, Trigger Eval)</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isSubmitting}>
              Send Invitation
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
