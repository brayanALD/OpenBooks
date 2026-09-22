import { ListingSkeleton } from "@/components/catalog/Listing";
import { Skeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <div className="flex flex-col gap-6">
      <Skeleton className="h-10 w-72" />
      <ListingSkeleton />
    </div>
  );
}
