"use client";

import { useState } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Pencil, Trash2, Database, ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Id, Doc } from "../../convex/_generated/dataModel";

type DatabaseDoc = Doc<"databases">;

interface DatabaseSelectorProps {
  selectedId: Id<"databases"> | null;
  onSelect: (id: Id<"databases"> | null) => void;
}

export function DatabaseSelector({ selectedId, onSelect }: DatabaseSelectorProps) {
  const databases = useQuery(api.databases.list);
  const createDatabase = useMutation(api.databases.create);
  const updateDatabase = useMutation(api.databases.update);
  const deleteDatabase = useMutation(api.databases.remove);

  const [isOpen, setIsOpen] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [newSystemPrompt, setNewSystemPrompt] = useState("");
  const [editingDb, setEditingDb] = useState<{
    id: Id<"databases">;
    name: string;
  } | null>(null);

  const selectedDatabase = databases?.find((db: DatabaseDoc) => db._id === selectedId);

  const handleCreate = async () => {
    if (!newName.trim()) return;

    try {
      const id = await createDatabase({
        name: newName.trim(),
        systemPrompt: newSystemPrompt.trim() || undefined,
      });
      onSelect(id);
      setNewName("");
      setNewSystemPrompt("");
      setIsCreateOpen(false);
    } catch (error) {
      console.error("Failed to create database:", error);
    }
  };

  const handleCreateDialogClose = (open: boolean) => {
    setIsCreateOpen(open);
    if (!open) {
      // Reset state when dialog closes
      setNewName("");
      setNewSystemPrompt("");
    }
  };

  const handleUpdate = async () => {
    if (!editingDb || !editingDb.name.trim()) return;

    try {
      await updateDatabase({
        id: editingDb.id,
        name: editingDb.name.trim(),
      });
      setIsEditOpen(false);
      setEditingDb(null);
    } catch (error) {
      console.error("Failed to update database:", error);
    }
  };

  const handleDelete = async () => {
    if (!selectedId) return;

    try {
      await deleteDatabase({ id: selectedId });
      onSelect(null);
      setIsDeleteOpen(false);
    } catch (error) {
      console.error("Failed to delete database:", error);
    }
  };

  const openCreateDialog = () => {
    setIsOpen(false);
    setIsCreateOpen(true);
  };

  const openEditDialog = (db: DatabaseDoc) => {
    setIsOpen(false);
    setEditingDb({
      id: db._id,
      name: db.name,
    });
    setIsEditOpen(true);
  };

  const openDeleteDialog = (db: DatabaseDoc) => {
    setIsOpen(false);
    onSelect(db._id);
    setIsDeleteOpen(true);
  };

  const selectDatabase = (id: Id<"databases">) => {
    onSelect(id);
    setIsOpen(false);
  };

  return (
    <>
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            role="combobox"
            aria-expanded={isOpen}
            className="justify-between"
          >
            <Database className="h-4 w-4 shrink-0 text-primary" />
            <span className="truncate">{selectedDatabase?.name ?? "Select database..."}</span>
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent
          className="w-[240px] p-0 overflow-hidden shadow-foreground/5 rounded-lg"
          align="end"
        >
          {/* Database List */}
          <div className="max-h-[200px] overflow-y-auto">
            {databases?.length === 0 ? (
              <div className="py-6 text-center text-sm text-muted-foreground">No databases yet</div>
            ) : (
              databases?.map((db: DatabaseDoc) => (
                <div
                  key={db._id}
                  className={cn(
                    "flex items-center justify-between px-2 pr-1 py-1 cursor-pointer hover:bg-accent group",
                    selectedId === db._id && "bg-accent"
                  )}
                >
                  <button
                    onClick={() => selectDatabase(db._id)}
                    className="flex items-center gap-2 flex-1 text-left text-sm"
                  >
                    <Check
                      className={cn(
                        "h-4 w-4 shrink-0",
                        selectedId === db._id ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <span className="truncate">{db.name}</span>
                  </button>
                  <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 hover:bg-foreground/5 rounded-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        openEditDialog(db);
                      }}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10 rounded-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        openDeleteDialog(db);
                      }}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Separator */}
          <div className="border-t" />

          {/* Create New Button */}
          <button
            onClick={openCreateDialog}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-accent transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Create new database</span>
          </button>
        </PopoverContent>
      </Popover>

      {/* Create Database Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={handleCreateDialogClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Database</DialogTitle>
            <DialogDescription>
              Create a new ICRL database to store examples and train your model.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 ">
            <div className="grid gap-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="My Database"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="system-prompt">Instructions (optional)</Label>
              <Textarea
                id="system-prompt"
                value={newSystemPrompt}
                onChange={(e) => setNewSystemPrompt(e.target.value)}
                placeholder="You are a helpful assistant that..."
                rows={4}
              />
              <p className="text-xs text-muted-foreground">
                Start your assistant off with a basic idea of what they should do. This doesn&apos;t
                have to be perfect, but will serve as a baseline for the in context RLHF process.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="secondary" size="sm" onClick={() => handleCreateDialogClose(false)}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleCreate} disabled={!newName.trim()}>
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Database Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Database</DialogTitle>
            <DialogDescription>Update the database name.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="edit-name">Name</Label>
              <Input
                id="edit-name"
                value={editingDb?.name ?? ""}
                onChange={(e) =>
                  setEditingDb((prev) => (prev ? { ...prev, name: e.target.value } : null))
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="secondary" size="sm" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleUpdate} disabled={!editingDb?.name.trim()}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Database</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &quot;{selectedDatabase?.name}&quot;? This action
              cannot be undone and will delete all examples in this database.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="secondary" size="sm" onClick={() => setIsDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" size="sm" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
