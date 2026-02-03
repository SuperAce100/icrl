"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CheckCircle2, ArrowRight } from "lucide-react";

interface SuccessMessageProps {
  message: string;
  onReset: () => void;
}

export function SuccessMessage({ message, onReset }: SuccessMessageProps) {
  return (
    <Card className="text-center">
      <CardHeader>
        <div className="mx-auto mb-4">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 text-primary">
            <CheckCircle2 className="h-8 w-8" />
          </div>
        </div>
        <CardTitle>Feedback Recorded!</CardTitle>
        <CardDescription>{message}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="bg-muted/50 rounded-lg p-4 max-w-md mx-auto">
          <p className="text-sm text-muted-foreground">
            Your preference has been added to the database. Future answers will
            be influenced by examples like this one, making the system better
            over time.
          </p>
        </div>

        <Button onClick={onReset}>
          Ask Another Question
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </CardContent>
    </Card>
  );
}
