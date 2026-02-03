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
  const [newDescription, setNewDescription] = useState("");
  const [editingDb, setEditingDb] = useState<{
    id: Id<"databases">;
    name: string;
    description: string;
  } | null>(null);

  const selectedDatabase = databases?.find((db: DatabaseDoc) => db._id === selectedId);

  const handleCreate = async () => {
    if (!newName.trim()) return;

    try {
      const id = await createDatabase({
        name: newName.trim(),
        description: newDescription.trim() || undefined,
      });
      onSelect(id);
      setNewName("");
      setNewDescription("");
      setIsCreateOpen(false);
    } catch (error) {
      console.error("Failed to create database:", error);
    }
  };

  const handleUpdate = async () => {
    if (!editingDb || !editingDb.name.trim()) return;

    try {
      await updateDatabase({
        id: editingDb.id,
        name: editingDb.name.trim(),
        description: editingDb.description.trim() || undefined,
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
      description: db.description ?? "",
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
            variant="outline"
            role="combobox"
            aria-expanded={isOpen}
            className="w-[200px] justify-between"
          >
            <div className="flex items-center gap-2 truncate">
              <Database className="h-4 w-4 shrink-0 text-muted-foreground" />
              <span className="truncate">{selectedDatabase?.name ?? "Select database..."}</span>
            </div>
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[240px] p-0" align="start">
          {/* Database List */}
          <div className="max-h-[200px] overflow-y-auto">
            {databases?.length === 0 ? (
              <div className="py-6 text-center text-sm text-muted-foreground">No databases yet</div>
            ) : (
              databases?.map((db: DatabaseDoc) => (
                <div
                  key={db._id}
                  className={cn(
                    "flex items-center justify-between px-2 py-1.5 cursor-pointer hover:bg-accent group",
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
                      className="h-7 w-7"
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
                      className="h-7 w-7 text-destructive hover:text-destructive"
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
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Database</DialogTitle>
            <DialogDescription>
              Create a new ICRL database to store examples and train your model.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
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
              <Label htmlFor="description">Description (optional)</Label>
              <Textarea
                id="description"
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="A database for..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={!newName.trim()}>
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Database Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Database</DialogTitle>
            <DialogDescription>Update the database name and description.</DialogDescription>
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
            <div className="grid gap-2">
              <Label htmlFor="edit-description">Description (optional)</Label>
              <Textarea
                id="edit-description"
                value={editingDb?.description ?? ""}
                onChange={(e) =>
                  setEditingDb((prev) => (prev ? { ...prev, description: e.target.value } : null))
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdate} disabled={!editingDb?.name.trim()}>
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
            <Button variant="outline" onClick={() => setIsDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
