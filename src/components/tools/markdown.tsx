import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Styled markdown renderer for tool results. Tuned to the Premium Dark
 * aesthetic — tight headings, tabular numbers in tables, emerald accents.
 */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="space-y-4 text-[14px] leading-relaxed text-foreground/90">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-balance text-2xl font-medium tracking-[-0.02em] text-foreground">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="mt-6 text-[18px] font-medium tracking-[-0.01em] text-foreground">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mt-5 text-[11px] uppercase tracking-[0.18em] text-brand">
              {children}
            </h3>
          ),
          p: ({ children }) => <p className="leading-relaxed">{children}</p>,
          ul: ({ children }) => (
            <ul className="list-disc space-y-1.5 pl-5 marker:text-brand/60">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal space-y-1.5 pl-5 marker:text-muted-foreground">
              {children}
            </ol>
          ),
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          strong: ({ children }) => (
            <strong className="font-medium text-foreground">{children}</strong>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-brand/50 pl-4 text-muted-foreground italic">
              {children}
            </blockquote>
          ),
          code: ({ children }) => (
            <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[12px] text-foreground">
              {children}
            </code>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto rounded-lg border border-border/60">
              <table className="numeric w-full text-left text-[13px]">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="border-b border-border/50 bg-card/60 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
              {children}
            </thead>
          ),
          th: ({ children }) => <th className="px-4 py-2.5 font-normal">{children}</th>,
          td: ({ children }) => (
            <td className="border-t border-border/30 px-4 py-2.5">{children}</td>
          ),
          a: ({ children, href }) => (
            <a
              href={href}
              className="text-brand underline-offset-4 hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
