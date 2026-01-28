"use client";

import { useState } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus, MoreVertical, Pencil, Trash2, Database } from "lucide-react";
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

  const openEditDialog = () => {
    if (selectedDatabase) {
      setEditingDb({
        id: selectedDatabase._id,
        name: selectedDatabase.name,
        description: selectedDatabase.description ?? "",
      });
      setIsEditOpen(true);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Database className="h-4 w-4 text-muted-foreground" />
      
      <Select
        value={selectedId ?? undefined}
        onValueChange={(value) => onSelect(value as Id<"databases">)}
      >
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Select database..." />
        </SelectTrigger>
        <SelectContent>
          {databases?.map((db: DatabaseDoc) => (
            <SelectItem key={db._id} value={db._id}>
              {db.name}
            </SelectItem>
          ))}
          {databases?.length === 0 && (
            <div className="py-2 px-2 text-sm text-muted-foreground">
              No databases yet
            </div>
          )}
        </SelectContent>
      </Select>

      {/* Create Database Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" size="icon">
            <Plus className="h-4 w-4" />
          </Button>
        </DialogTrigger>
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

      {/* Database Actions Menu */}
      {selectedId && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={openEditDialog}>
              <Pencil className="mr-2 h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => setIsDeleteOpen(true)}
              className="text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}

      {/* Edit Database Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Database</DialogTitle>
            <DialogDescription>
              Update the database name and description.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="edit-name">Name</Label>
              <Input
                id="edit-name"
                value={editingDb?.name ?? ""}
                onChange={(e) =>
                  setEditingDb((prev) =>
                    prev ? { ...prev, name: e.target.value } : null
                  )
                }
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit-description">Description (optional)</Label>
              <Textarea
                id="edit-description"
                value={editingDb?.description ?? ""}
                onChange={(e) =>
                  setEditingDb((prev) =>
                    prev ? { ...prev, description: e.target.value } : null
                  )
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
              Are you sure you want to delete &quot;{selectedDatabase?.name}&quot;? This
              action cannot be undone and will delete all examples in this
              database.
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
    </div>
  );
}
