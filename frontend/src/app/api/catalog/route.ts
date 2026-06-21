import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export function GET() {
  return NextResponse.json({
    catalog: [
      {
        id: "cell-analytics-control-plane",
        title: "Cell Analytics Control Plane",
        category: "dashboard",
        href: "/",
      },
    ],
  });
}
