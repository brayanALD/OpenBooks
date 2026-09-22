import { endSession } from "@/lib/route-handlers";

export const POST = (request: Request) => endSession(request);
