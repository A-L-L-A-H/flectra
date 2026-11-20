# Shared UI

This workspace owns the editable React component source shared by Flectra frontend applications.

Components follow the shadcn/ui new-york conventions and use Radix UI primitives where appropriate. The source lives in `src/components`; it is not a runtime dependency on a hosted component library.

## Add more shadcn/ui components

Run the CLI from the Next.js app workspace so it can resolve the monorepo aliases:

```bash
cd apps/web
pnpm dlx shadcn@latest add dialog
```

The CLI configuration is in `apps/web/components.json` and `packages/ui/components.json`. Review generated imports and dependencies before committing new components.
