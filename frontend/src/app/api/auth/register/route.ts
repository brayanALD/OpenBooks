import { startSession } from "@/lib/route-handlers";

export const POST = (request: Request) => startSession(request, "/auth/register", 201);
