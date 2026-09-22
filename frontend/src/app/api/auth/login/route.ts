import { startSession } from "@/lib/route-handlers";

export const POST = (request: Request) => startSession(request, "/auth/login", 200);
