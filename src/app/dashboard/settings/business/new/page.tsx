import { AddBusinessForm } from "@/components/dashboard/business/add-business-form";

export default function NewBusinessPage() {
  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Add New Business</h1>
          <p className="text-muted-foreground">
            Create a new business to track expenses separately
          </p>
        </div>
        <AddBusinessForm />
      </div>
    </div>
  );
} 