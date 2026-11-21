import { FileWarning, Lock } from "lucide-react";
import { Badge } from "@moonwitness/ui/components/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@moonwitness/ui/components/card";
import { formatFieldValue, type ParsedFormView } from "@/lib/form-view";

export function ModelFormView({
  form,
  record,
}: {
  form: ParsedFormView;
  record: Record<string, unknown>;
}) {
  if (!form.ok) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-amber-500/10 text-amber-700">
              <FileWarning className="size-4" />
            </div>
            <div>
              <CardTitle className="text-base">Form layout unavailable</CardTitle>
              <CardDescription>{form.message}</CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {form.sections.map((section) => (
        <Card key={section.id}>
          <CardHeader className="border-b border-border">
            <CardTitle className="text-base">{section.title}</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <dl className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
              {section.items.map((item, index) => {
                if (item.kind === "unsupported") {
                  return (
                    <div key={`${item.name}-${index}`} className="space-y-1.5 sm:col-span-2">
                      <dt className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                        <span>{item.label}</span>
                        <Badge variant="outline" className="text-[10px] font-normal">
                          Read-only placeholder
                        </Badge>
                      </dt>
                      <dd className="flex items-center gap-2 rounded-md border border-dashed border-border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
                        <Lock className="size-3.5 shrink-0" />
                        <span>{item.reason}</span>
                      </dd>
                    </div>
                  );
                }

                const formatted = formatFieldValue(record[item.name], item, record);
                const isMultiline = item.fieldType === "text";

                return (
                  <div
                    key={`${item.name}-${index}`}
                    className={isMultiline ? "space-y-1 sm:col-span-2" : "space-y-1"}
                  >
                    <dt className="text-xs font-medium text-muted-foreground">{item.label}</dt>
                    <dd
                      className={
                        isMultiline
                          ? "whitespace-pre-wrap rounded-md border border-border/60 bg-muted/20 p-3 text-sm text-foreground"
                          : "break-words text-sm text-foreground"
                      }
                    >
                      {formatted}
                    </dd>
                  </div>
                );
              })}
            </dl>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
