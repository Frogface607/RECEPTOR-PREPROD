import {
  ChefHat,
  Users,
  Megaphone,
  BarChart3,
  UserPlus,
  Shield,
  Utensils,
  Calculator,
  DollarSign,
  AlertTriangle,
  Lightbulb,
  MessageSquare,
  FileText,
  MessageCircle,
  Share2,
  Scale,
  Sparkles,
  Target,
  ClipboardList,
  Briefcase,
  ListChecks,
  ShieldCheck,
  FileCheck,
  XCircle,
  Wine,
  ClipboardCheck,
  Sun,
  TrendingDown,
  AlertCircle,
  GraduationCap,
  PartyPopper,
  Leaf,
  Wrench,
  type LucideIcon,
} from "lucide-react";

/**
 * Explicit name → component map for every icon referenced in the tools
 * catalog. Explicit (not dynamic) so bundler tree-shaking keeps it lean and
 * a typo surfaces as a fallback rather than a crash.
 */
const ICON_MAP: Record<string, LucideIcon> = {
  ChefHat,
  Users,
  Megaphone,
  BarChart3,
  UserPlus,
  Shield,
  Utensils,
  Calculator,
  DollarSign,
  AlertTriangle,
  Lightbulb,
  MessageSquare,
  FileText,
  MessageCircle,
  Share2,
  Scale,
  Sparkles,
  Target,
  ClipboardList,
  Briefcase,
  ListChecks,
  ShieldCheck,
  FileCheck,
  XCircle,
  Wine,
  ClipboardCheck,
  Sun,
  TrendingDown,
  AlertCircle,
  GraduationCap,
  PartyPopper,
  Leaf,
};

export function ToolIcon({
  name,
  className,
}: {
  name: string;
  className?: string;
}) {
  const Icon = ICON_MAP[name] ?? Wrench;
  return <Icon className={className} />;
}
