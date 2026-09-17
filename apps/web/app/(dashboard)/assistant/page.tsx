import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { ChatArea } from '@/components/chat/ChatArea';

export default function AssistantPage() {
  return <ResponsivePageContainer>
    <PageHeader title="Ask your Second Brain" description="Find saved context and open the sources behind each answer." badge="CLOSED BETA" />
    <p className="text-sm text-muted-foreground">Answers use matching saved records. When AI is unavailable, you will see clearly labelled source excerpts. Review sources before acting on an answer.</p>
    <div className="my-6"><ChatArea subtitle="Answers from your saved context" /></div>
  </ResponsivePageContainer>;
}
