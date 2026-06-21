import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export function GET() {
  return NextResponse.json({
    featured: [
      {
        id: "default-cell-simulation",
        title: "Default Cell Simulation",
        description: "Authenticated starter scenario for the Preon Systems cell engine.",
        href: "/",
      },
    ],
  });
}
