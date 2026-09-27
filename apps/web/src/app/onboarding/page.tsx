import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard";

export const metadata = {
  title: "Onboarding Wizard | SROT Enterprise RAG",
  description: "Set up your tenant workspace and configure your AI model provider.",
};

export default function OnboardingPage() {
  return <OnboardingWizard />;
}
