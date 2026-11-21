import type { Metadata } from "next";
import { ModelListView } from "@/components/model-list-view";

type ModelPageProps = {
  params: Promise<{ model: string }>;
};

export async function generateMetadata({ params }: ModelPageProps): Promise<Metadata> {
  const { model } = await params;
  return { title: model };
}

export default async function ModelPage({ params }: ModelPageProps) {
  const { model } = await params;
  return <ModelListView model={decodeURIComponent(model)} />;
}
