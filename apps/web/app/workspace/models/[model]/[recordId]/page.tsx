import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ModelRecordDetailView } from "@/components/model-record-detail-view";
import { isValidModelName, parsePositiveRecordId } from "@/lib/record-detail";

type RecordDetailPageProps = {
  params: Promise<{ model: string; recordId: string }>;
};

export async function generateMetadata({ params }: RecordDetailPageProps): Promise<Metadata> {
  const { model, recordId } = await params;
  const decodedModel = decodeURIComponent(model);
  const parsedId = parsePositiveRecordId(decodeURIComponent(recordId));
  if (!isValidModelName(decodedModel) || parsedId === null) {
    return { title: "Record not found" };
  }
  return { title: `${decodedModel} #${parsedId}` };
}

export default async function ModelRecordDetailPage({ params }: RecordDetailPageProps) {
  const { model, recordId } = await params;
  const decodedModel = decodeURIComponent(model);
  const parsedId = parsePositiveRecordId(decodeURIComponent(recordId));

  // Validate model and record ID before any upstream RPC call.
  if (!isValidModelName(decodedModel) || parsedId === null) {
    notFound();
  }

  return <ModelRecordDetailView model={decodedModel} recordId={parsedId} />;
}
