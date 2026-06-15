import {
  AssessmentAuthoringSummary,
  AssignmentSubmissionState,
  AttemptStatusPanel,
  CertificateCard,
  CourseCard,
  CourseStructureTree,
  GradingReviewPanel,
  LessonPlayerLayout,
  NotificationFeed,
  ProgressIndicator,
  ReportingFilters,
  ReportInsightPanel,
  RubricCommentBox
} from '../lms/LmsProductComponents';
import {
  Badge,
  Button,
  Card,
  CheckboxField,
  DataTable,
  DateTimeField,
  Divider,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  PageHeader,
  PermissionDeniedState,
  RadioField,
  Select,
  SkeletonBlock,
  Tabs,
  Tag,
  Textarea,
  Toast
} from '../shared/ui';

const sampleCourse = {
  id: 'course-preview',
  title: 'Learning Management Foundations',
  description: 'A representative catalog card for LearnGrid course discovery.',
  status: 'published',
  difficulty_level: 'beginner',
  categories: [{ id: 'cat-1', name: 'Operations' }],
  tags: [{ id: 'tag-1', name: 'LMS' }],
  prerequisite_course_ids: ['course-intro'],
  learning_outcomes: [{ id: 'outcome-1', description: 'Describe LMS workflows.' }]
};

const sampleStructure = {
  ...sampleCourse,
  modules: [
    {
      id: 'module-1',
      title: 'Module one',
      lessons: [
        {
          id: 'lesson-1',
          title: 'Welcome lesson',
          status: 'draft',
          summary: 'A lesson summary',
          content_asset_id: 'asset-1',
          topics: [{ id: 'topic-1', title: 'Topic one', content_asset_id: 'asset-2' }]
        }
      ]
    }
  ]
};

export function DesignSystemPreview() {
  return (
    <main className="space-y-8 bg-slate-50 p-6">
      <PageHeader
        eyebrow="T-028 evidence"
        title="LearnGrid UI Design System Preview"
        description="Component-preview documentation for tokens, primitives, LMS product components, and representative states."
        breadcrumbs={[{ label: 'Frontend' }, { label: 'Design system' }]}
      >
        <Button>Primary action</Button>
        <Button variant="secondary">Secondary</Button>
      </PageHeader>

      <section className="grid gap-4 lg:grid-cols-3" aria-label="Design tokens">
        <Card>
          <h2 className="font-semibold text-slate-950">Color tokens</h2>
          <div className="mt-4 grid grid-cols-3 gap-2">
            <span className="h-12 rounded-control bg-emerald-700" role="img" aria-label="brand emerald" />
            <span className="h-12 rounded-control bg-blue-600" role="img" aria-label="info blue" />
            <span className="h-12 rounded-control bg-rose-700" role="img" aria-label="danger rose" />
          </div>
        </Card>
        <Card>
          <h2 className="font-semibold text-slate-950">Status chips</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            <Badge tone="success">success</Badge>
            <Badge tone="warning">warning</Badge>
            <Badge tone="error">error</Badge>
            <Tag>metadata tag</Tag>
          </div>
        </Card>
        <Card>
          <h2 className="font-semibold text-slate-950">Buttons</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button size="sm">Small</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Delete</Button>
            <Button loading>Saving</Button>
          </div>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-2" aria-label="Forms and feedback">
        <Card>
          <h2 className="font-semibold text-slate-950">Form controls</h2>
          <div className="mt-4 grid gap-3">
            <Field htmlFor="preview-input" label="Input" required helpText="Required marker and help text are built in.">
              <Input id="preview-input" placeholder="Course title" />
            </Field>
            <Field htmlFor="preview-select" label="Select">
              <Select id="preview-select">
                <option>Published</option>
                <option>Draft</option>
              </Select>
            </Field>
            <Field htmlFor="preview-textarea" label="Textarea">
              <Textarea id="preview-textarea" rows={3} />
            </Field>
            <CheckboxField label="Checkbox control" helpText="Used for binary settings." />
            <RadioField label="Radio control" name="preview-radio" />
            <DateTimeField htmlFor="preview-date" label="Date field" />
          </div>
        </Card>
        <div className="space-y-4">
          <SkeletonBlock />
          <ErrorState title="Retry state" error={new Error('API denied this request.')} />
          <EmptyState message="Useful empty state with a call to action." action={<Button variant="secondary">Create first item</Button>} />
          <PermissionDeniedState />
          <Toast title="Toast notification" message="Non-blocking feedback uses status tone colors." tone="success" />
        </div>
      </section>

      <Divider label="Product components" />

      <section className="grid gap-4 xl:grid-cols-2" aria-label="LMS product components">
        <CourseCard course={sampleCourse} href="/dashboard/student/courses/course-preview" />
        <CourseStructureTree structure={sampleStructure} mode="author" />
        <LessonPlayerLayout
          lessonTitle="Welcome lesson"
          summary="Document and video display states share one lesson player shell."
          assetId="asset-1"
          outline={<CourseStructureTree structure={sampleStructure} />}
          actions={<Button>Mark complete</Button>}
        />
        <AttemptStatusPanel status="in_progress" timeRemaining="24:00" autosaveState="Saved 20 seconds ago">
          <Button>Submit attempt</Button>
        </AttemptStatusPanel>
        <AssignmentSubmissionState submissionId="submission-1" deadline="2026-06-30" />
        <GradingReviewPanel record={{ id: 'grade-1', status: 'calculated', score: 88, max_score: 100 }}>
          <RubricCommentBox>
            <Button variant="secondary">Save comments</Button>
          </RubricCommentBox>
        </GradingReviewPanel>
        <CertificateCard certificate={{ id: 'cert-1', certificate_number: 'LG-20260615-ABCDEF1234', valid: true, course_id: 'course-preview' }} />
        <NotificationFeed notifications={[{ id: 'notice-1', title: 'Grade published', event_type: 'GradePublished', read_at: null }]} />
        <ReportInsightPanel title="Report snapshots" items={[{ id: 'report-1', title: 'Active users report', status: 'ready' }]} />
        <Card>
          <h2 className="font-semibold text-slate-950">Analytics filters and data table</h2>
          <div className="mt-4 space-y-4">
            <ReportingFilters q="" resourceType="all" onQChange={() => undefined} onResourceTypeChange={() => undefined} />
            <ProgressIndicator value={67} />
            <DataTable
              columns={[
                { key: 'name', header: 'Name' },
                { key: 'status', header: 'Status' }
              ]}
              rows={[{ id: 'row-1', name: 'Course completion', status: 'ready' }]}
            />
            <Tabs
              value="student"
              onChange={() => undefined}
              items={[
                { key: 'student', label: 'Student' },
                { key: 'instructor', label: 'Instructor' },
                { key: 'admin', label: 'Admin' }
              ]}
            />
          </div>
        </Card>
      </section>

      <AssessmentAuthoringSummary banks={[{ id: 'bank-1', title: 'Bank' }]} assessments={[{ id: 'assessment-1', title: 'Quiz' }]} />
      <Modal title="Modal preview" open={false}>
        Hidden by default
      </Modal>
    </main>
  );
}
