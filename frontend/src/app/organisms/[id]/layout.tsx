"use client";

import { use } from "react";
import { OrganismDetailProvider } from "@/lib/organism-detail-context";
import { OrganismNav } from "@/components/layout/organism-nav";

export default function OrganismDetailLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return (
    <OrganismDetailProvider id={id}>
      <div className="flex h-full flex-col">
        <OrganismNav id={id} />
        <div className="flex-1 overflow-auto">{children}</div>
      </div>
    </OrganismDetailProvider>
  );
}
