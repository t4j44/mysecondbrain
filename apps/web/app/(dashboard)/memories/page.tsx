import {SavedRecordList} from '@/components/shared/saved-record-list';
export default function Page(){return <SavedRecordList title="Saved notes" description="Your saved notes and reflections. Open a record to check its original context." endpoint="/memories" kind="memory" createHref="/memories/new" createLabel="Add a note"/>;}
