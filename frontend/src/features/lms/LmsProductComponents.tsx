import {
  BarChart3,
  Bell,
  BookOpen,
  Award,
  ClipboardList,
  FileText,
  GraduationCap,
  ListTree,
  PlayCircle,
  Timer
} from 'lucide-react';
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

import type { Course, CourseStructure } from '../../api/courses';
import type { Certificate, GradeRecord } from '../../api/grading';
import type { NotificationItem } from '../../api/notifications';
import type { Entity } from '../../api/types';
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Field,
  Input,
  metadataLine,
  Panel,
  PaginationControls,
  Select,
  StatusBadge,
  Tag,
  Textarea,
  itemTitle
} from '../shared/ui';

function percent(value: unknown) {
  if (typeof value === 'number') {
    return `${Math.round(value)}%`;
  }
  if (typeof value === 'string' && value) {
    return value.endsWith('%') ? value : `${value}%`;
  }
  return '0%';
}

export function CourseCard({
  course,
  href,
  cta = 'View course'
}: {
  course: Course;
  href: string;
  cta?: string;
}) {
  return (
    <Card interactive>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <BookOpen className="h-5 w-5 text-emerald-700" aria-hidden />
            <h3 className="text-lg font-semibold text-slate-950">{itemTitle(course)}</h3>
            <StatusBadge value={course.status} />
          </div>
          <p className="mt-2 line-clamp-3 text-sm leading-6 text-slate-600">
            {String(course.description || 'No course description provided.')}
          </p>
        </div>
        <Badge tone={course.difficulty_level ? 'info' : 'neutral'}>
          {course.difficulty_level || 'unspecified'}
        </Badge>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {(course.categories ?? []).slice(0, 3).map((category) => (
          <Tag key={category.id}>{itemTitle(category)}</Tag>
        ))}
        {(course.tags ?? []).slice(0, 3).map((tag) => (
          <Tag key={tag.id}>{itemTitle(tag)}</Tag>
        ))}
        {!(course.categories?.length || course.tags?.length) ? <Tag>No metadata</Tag> : null}
      </div>
      <div className="mt-5 flex items-center justify-between gap-3">
        <span className="text-xs text-slate-500">
          {(course.learning_outcomes ?? []).length} outcomes · {(course.prerequisite_course_ids ?? []).length} prerequisites
        </span>
        <Link className="text-sm font-semibold text-emerald-700 hover:underline" to={href}>
          {cta}
        </Link>
      </div>
    </Card>
  );
}

export function CourseCatalogFilters({
  q,
  status,
  difficulty,
  page,
  onQChange,
  onStatusChange,
  onDifficultyChange,
  onPrevious,
  onNext
}: {
  q: string;
  status: string;
  difficulty: string;
  page: number;
  onQChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onDifficultyChange: (value: string) => void;
  onPrevious: () => void;
  onNext: () => void;
}) {
  return (
    <section className="mb-5 rounded-panel border border-slate-200 bg-white p-4 shadow-panel">
      <div className="grid gap-3 lg:grid-cols-[1fr_180px_180px_auto]">
        <Field htmlFor="catalog-q" label="Search" helpText="Find by course title or description.">
          <Input id="catalog-q" value={q} onChange={(event) => onQChange(event.target.value)} />
        </Field>
        <Field htmlFor="catalog-status" label="Status">
          <Select id="catalog-status" value={status} onChange={(event) => onStatusChange(event.target.value)}>
            <option value="published">Published</option>
            <option value="">Any permitted status</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </Select>
        </Field>
        <Field htmlFor="catalog-difficulty" label="Difficulty">
          <Select id="catalog-difficulty" value={difficulty} onChange={(event) => onDifficultyChange(event.target.value)}>
            <option value="">Any</option>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </Select>
        </Field>
        <div className="flex items-end">
          <PaginationControls page={page} onPrevious={onPrevious} onNext={onNext} />
        </div>
      </div>
    </section>
  );
}

export function CourseDetailHeader({
  course,
  actions
}: {
  course: Course;
  actions?: ReactNode;
}) {
  return (
    <Card className="mb-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <BookOpen className="h-5 w-5 text-emerald-700" aria-hidden />
            <h2 className="text-2xl font-semibold text-slate-950">{itemTitle(course)}</h2>
            <StatusBadge value={course.status} />
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
            {String(course.description || 'No course description provided.')}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Badge tone="info">{course.difficulty_level || 'difficulty not set'}</Badge>
            <Badge>{(course.categories ?? []).length} categories</Badge>
            <Badge>{(course.tags ?? []).length} tags</Badge>
          </div>
        </div>
        {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
      </div>
    </Card>
  );
}

export function CourseStructureTree({
  structure,
  mode = 'read',
  onPublishLesson
}: {
  structure: CourseStructure;
  mode?: 'read' | 'author';
  onPublishLesson?: (lessonId: string) => void;
}) {
  const modules = structure.modules ?? [];
  if (!modules.length) {
    return <EmptyState message="No modules are available yet." />;
  }
  return (
    <div className="space-y-4">
      {modules.map((module, moduleIndex) => (
        <section className="rounded-panel border border-slate-200 p-4" key={module.id}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <ListTree className="h-4 w-4 text-emerald-700" aria-hidden />
                <Badge tone="neutral">Module {moduleIndex + 1}</Badge>
                <h4 className="font-semibold text-slate-950">{itemTitle(module)}</h4>
              </div>
              {mode === 'author' ? <p className="mt-1 text-xs text-slate-500">Module ID: {module.id}</p> : null}
            </div>
            {mode === 'author' ? <Tag>Drag order planned</Tag> : null}
          </div>
          <ul className="mt-3 space-y-2">
            {(module.lessons ?? []).map((lesson, lessonIndex) => (
              <li className="rounded-panel bg-slate-50 p-3 text-sm" key={lesson.id}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <PlayCircle className="h-4 w-4 text-blue-700" aria-hidden />
                      <Badge tone="info">Lesson {lessonIndex + 1}</Badge>
                      <span className="font-medium text-slate-900">{itemTitle(lesson)}</span>
                      <StatusBadge value={String(lesson.status ?? 'draft')} />
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {lesson.content_asset_id ? `Attached asset ${lesson.content_asset_id}` : 'No content asset attached'}
                    </p>
                  </div>
                  {mode === 'author' ? (
                    <Button variant="secondary" size="sm" onClick={() => onPublishLesson?.(lesson.id)}>
                      Publish lesson
                    </Button>
                  ) : null}
                </div>
                {lesson.topics?.length ? (
                  <ul className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
                    {lesson.topics.map((topic) => (
                      <li className="rounded-control border border-slate-200 bg-white px-3 py-2" key={topic.id}>
                        {itemTitle(topic)} · {topic.content_asset_id || 'no asset'}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-xs text-slate-500">No topics yet.</p>
                )}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

export function LessonPlayerLayout({
  lessonTitle,
  summary,
  assetId,
  outline,
  actions,
  accessDenied
}: {
  lessonTitle: string;
  summary?: string | null;
  assetId?: string | null;
  outline: ReactNode;
  actions?: ReactNode;
  accessDenied?: boolean;
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
      <Panel title={lessonTitle} description={accessDenied ? 'Access is blocked by backend authorization.' : 'Use the controls below to update learning progress.'}>
        {accessDenied ? (
          <EmptyState message="This lesson is not available to your current role or enrollment." />
        ) : (
          <div className="space-y-4 text-sm text-slate-700">
            <p>{summary || 'This lesson has no summary yet.'}</p>
            <div className="rounded-panel border border-slate-200 bg-slate-50 p-4">
              <h4 className="flex items-center gap-2 font-semibold text-slate-950">
                <FileText className="h-4 w-4 text-emerald-700" aria-hidden />
                Content display
              </h4>
              <p className="mt-2 text-slate-600">
                {assetId ? `Content asset ${assetId}` : 'No content asset is attached to this lesson.'}
              </p>
            </div>
            {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
          </div>
        )}
      </Panel>
      <Panel title="Course outline">{outline}</Panel>
    </div>
  );
}

export function AssessmentAuthoringSummary({
  banks,
  assessments
}: {
  banks: Entity[];
  assessments: Entity[];
}) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Card>
        <div className="text-xs font-semibold uppercase text-slate-500">Question banks</div>
        <div className="mt-2 flex items-center gap-2 text-2xl font-semibold text-slate-950">
          <ClipboardList className="h-5 w-5 text-emerald-700" aria-hidden />
          {banks.length}
        </div>
        <p className="mt-1 text-xs text-slate-500">Reusable banks available for authoring.</p>
      </Card>
      <Card>
        <div className="text-xs font-semibold uppercase text-slate-500">Assessments</div>
        <div className="mt-2 flex items-center gap-2 text-2xl font-semibold text-slate-950">
          <Timer className="h-5 w-5 text-blue-700" aria-hidden />
          {assessments.length}
        </div>
        <p className="mt-1 text-xs text-slate-500">Draft, published, and closed assessment records.</p>
      </Card>
    </div>
  );
}

export function AttemptStatusPanel({
  status,
  timeRemaining,
  autosaveState,
  children
}: {
  status?: string | null;
  timeRemaining?: string;
  autosaveState?: string;
  children?: ReactNode;
}) {
  return (
    <Panel
      title="Attempt status"
      actions={<StatusBadge value={status || 'not_started'} />}
      description="Timers, autosave, draft answers, and final submission state are visible before action."
    >
      <div className="grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <div className="text-xs font-semibold uppercase text-slate-500">Time remaining</div>
          <div className="mt-1 font-medium text-slate-950">{timeRemaining || 'Not started'}</div>
        </div>
        <div>
          <div className="text-xs font-semibold uppercase text-slate-500">Autosave</div>
          <div className="mt-1 font-medium text-slate-950">{autosaveState || 'No draft changes'}</div>
        </div>
      </div>
      {children ? <div className="mt-4">{children}</div> : null}
    </Panel>
  );
}

export function AssignmentSubmissionState({
  submissionId,
  deadline,
  late,
  closed
}: {
  submissionId?: string;
  deadline?: string;
  late?: boolean;
  closed?: boolean;
}) {
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="flex items-center gap-2 font-semibold text-slate-950">
            <FileText className="h-4 w-4 text-emerald-700" aria-hidden />
            Submission state
          </h3>
          <p className="mt-1 text-sm text-slate-600">
            {submissionId ? `Draft ID ${submissionId}` : 'No draft has been saved yet.'}
          </p>
        </div>
        <StatusBadge value={closed ? 'closed' : late ? 'late' : submissionId ? 'draft' : 'not_started'} />
      </div>
      <p className="mt-3 text-xs text-slate-500">{deadline ? `Deadline: ${deadline}` : 'No deadline shown by the current API response.'}</p>
    </Card>
  );
}

export function GradingReviewPanel({
  record,
  children
}: {
  record?: GradeRecord;
  children?: ReactNode;
}) {
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-950">Review and publication</h3>
          <p className="mt-1 text-sm text-slate-600">
            {record ? metadataLine(record, ['student_profile_id', 'course_id', 'score', 'max_score']) : 'Select a record for review.'}
          </p>
        </div>
        <StatusBadge value={record?.status} />
      </div>
      {children ? <div className="mt-4">{children}</div> : null}
    </Card>
  );
}

export function CertificateCard({
  certificate,
  action
}: {
  certificate: Certificate;
  action?: ReactNode;
}) {
  const revoked = Boolean(certificate.revoked_at) || certificate.valid === false;
  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-slate-950">{certificate.certificate_number || itemTitle(certificate)}</h3>
            <Award className="h-4 w-4 text-emerald-700" aria-hidden />
            <StatusBadge value={revoked ? 'revoked' : 'valid'} />
          </div>
          <p className="mt-2 text-sm text-slate-600">
            Course {String(certificate.course_id || 'not specified')} · Student {String(certificate.student_profile_id || 'not specified')}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Asset: {certificate.certificate_asset_id || 'not linked'}
          </p>
        </div>
        {action}
      </div>
    </Card>
  );
}

export function NotificationFeed({
  notifications,
  actions
}: {
  notifications: NotificationItem[];
  actions?: (notification: NotificationItem) => ReactNode;
}) {
  if (!notifications.length) {
    return <EmptyState message="No notifications yet." />;
  }
  return (
    <ul className="divide-y divide-slate-100 rounded-panel border border-slate-200 bg-white shadow-panel">
      {notifications.map((notification) => (
        <li className="flex flex-wrap items-start justify-between gap-3 p-4" key={notification.id}>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-medium text-slate-950">{itemTitle(notification)}</h3>
              <Bell className="h-4 w-4 text-blue-700" aria-hidden />
              <StatusBadge value={notification.read_at ? 'read' : 'unread'} />
            </div>
            <p className="mt-1 text-sm text-slate-600">{notification.body || notification.event_type || 'Notification event'}</p>
            <p className="mt-1 text-xs text-slate-500">{metadataLine(notification, ['event_type', 'created_at'])}</p>
          </div>
          {actions ? <div className="flex flex-wrap gap-2">{actions(notification)}</div> : null}
        </li>
      ))}
    </ul>
  );
}

export function ReportInsightPanel({
  title,
  items,
  action
}: {
  title: string;
  items: Entity[];
  action?: ReactNode;
}) {
  return (
    <Panel title={title} actions={action}>
      {items.length ? (
        <div className="grid gap-3">
          {items.slice(0, 5).map((item) => (
            <Card className="p-4" key={item.id}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="font-medium text-slate-950">{itemTitle(item)}</span>
                <BarChart3 className="h-4 w-4 text-emerald-700" aria-hidden />
                <StatusBadge value={item.status} />
              </div>
              <p className="mt-1 text-xs text-slate-500">{metadataLine(item)}</p>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState message={`No ${title.toLowerCase()} yet.`} />
      )}
    </Panel>
  );
}

export function ReportingFilters({
  q,
  resourceType,
  onQChange,
  onResourceTypeChange
}: {
  q: string;
  resourceType: string;
  onQChange: (value: string) => void;
  onResourceTypeChange: (value: string) => void;
}) {
  return (
    <section className="rounded-panel border border-slate-200 bg-white p-4 shadow-panel">
      <div className="grid gap-3 md:grid-cols-[1fr_220px]">
        <Field htmlFor="analytics-q" label="Search">
          <Input id="analytics-q" value={q} onChange={(event) => onQChange(event.target.value)} />
        </Field>
        <Field htmlFor="analytics-resource" label="Resource">
          <Select id="analytics-resource" value={resourceType} onChange={(event) => onResourceTypeChange(event.target.value)}>
            <option value="all">All permitted</option>
            <option value="courses">Courses</option>
            <option value="users">Users</option>
            <option value="enrollments">Enrollments</option>
            <option value="assessments">Assessments</option>
            <option value="submissions">Submissions</option>
          </Select>
        </Field>
      </div>
    </section>
  );
}

export function RubricCommentBox({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-panel border border-slate-200 bg-slate-50 p-4">
      <h3 className="font-semibold text-slate-950">Rubric comments and override notes</h3>
      <GraduationCap className="mt-2 h-4 w-4 text-emerald-700" aria-hidden />
      <div className="mt-3">
        <Textarea aria-label="Rubric comments" rows={4} placeholder="Add grading comments, override reason, or reviewer feedback." />
      </div>
      {children ? <div className="mt-3">{children}</div> : null}
    </div>
  );
}

export function ProgressIndicator({ value }: { value?: string | number }) {
  const display = percent(value);
  const numeric = Number(String(display).replace('%', '')) || 0;
  return (
    <div>
      <div className="flex justify-between text-xs font-medium text-slate-600">
        <span>Progress</span>
        <span>{display}</span>
      </div>
      <div className="mt-1 h-2 rounded-full bg-slate-200">
        <div className="h-2 rounded-full bg-emerald-700" style={{ width: `${Math.min(100, Math.max(0, numeric))}%` }} />
      </div>
    </div>
  );
}
