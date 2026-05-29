import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";
import { Hero } from "@/components/marketing/hero";
import { ProblemSolution } from "@/components/marketing/problem-solution";
import { LiveSnapshot } from "@/components/marketing/live-snapshot";
import { Cases } from "@/components/marketing/cases";
import { PricingTeaser } from "@/components/marketing/pricing-teaser";

export default function HomePage() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <Hero />
        <ProblemSolution />
        <LiveSnapshot />
        <Cases />
        <PricingTeaser />
      </main>
      <SiteFooter />
    </>
  );
}
