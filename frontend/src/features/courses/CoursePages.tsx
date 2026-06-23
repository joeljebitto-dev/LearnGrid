import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState, type FormEvent, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  listRoleAssignments,
  type RoleAssignment,
  type SessionContext
} from '../../api/auth';
import {
  closeAssessment,
  createAssessment,
  createQuestion,
  createQuestionBank,
  listAssessments,
  listQuestionBanks,
  listQuestions,
  publishAssessment,
  replaceAssessmentQuestions,
  updateAssessment,
  type Assessment
} from '../../api/assessments';
import {
  createLesson,
  createModule,
  createTopic,
  getCourse,
  getCourseStructure,
  listCourses,
  publishLesson,
  type Course
} from '../../api/courses';
import { createEnrollment, listEnrollments, type Enrollment } from '../../api/enrollments';
import { createSignedAccess } from '../../api/content';
import { updateLessonProgress, updateVideoProgress } from '../../api/progress';
import { toList } from '../../api/types';
import { PortalLayout } from '../layout/PortalLayout';
import {
  CourseCard,
  CourseCatalogFilters,
  CourseDetailHeader,
  CourseStructureTree,
  LessonPlayerLayout
} from '../lms/LmsProductComponents';
import { useUnsavedChangesWarning } from '../shared/quality';
import {
  Button,
  EmptyState,
  ErrorState,
  fieldClass,
  Field,
  JsonPreview,
  LoadingState,
  Modal,
  PageHeader,
  Panel,
  parseCsv,
  itemTitle,
  secondaryButtonClass,
  StatusBadge
} from '../shared/ui';

function studentBreadcrumbs(items: Array<{ label: string; href?: string }> = []) {
  return [{ label: 'Student', href: '/dashboard/student' }, ...items];
}

function studentCourseBreadcrumbs(courseId: string, title?: string, tail?: string) {
  return studentBreadcrumbs([
    { label: 'Courses', href: '/dashboard/student/courses' },
    {
      label: title || 'Course',
      href: tail ? `/dashboard/student/courses/${courseId}` : undefined
    },
    ...(tail ? [{ label: tail }] : [])
  ]);
}

function useCourseFilters(context: SessionContext) {
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('published');
  const [difficulty, setDifficulty] = useState('');
  const [page, setPage] = useState(1);
  const params = useMemo(
    () => ({
      q,
      status,
      difficulty_level: difficulty,
      institution_id: context.profile.institution_id ?? undefined,
      page,
      page_size: 10,
      sort: '-updated_at'
    }),
    [context.profile.institution_id, difficulty, page, q, status]
  );
  return { q, setQ, status, setStatus, difficulty, setDifficulty, page, setPage, params };
}

export function CourseCatalogPage({ context }: { context: SessionContext }) {
  const filters = useCourseFilters(context);
  const query = useQuery({
    queryKey: ['courses', 'catalog', filters.params],
    queryFn: () => listCourses(filters.params)
  });
  const courses = toList(query.data);

  return (
    <PortalLayout context={context} activeNav="student-courses">
      <PageHeader
        title="Course Catalog"
        description="Browse published courses with search, filters, pagination, and backend permission checks."
        breadcrumbs={studentBreadcrumbs([{ label: 'Courses' }])}
      />
      <CourseCatalogFilters
        q={filters.q}
        status={filters.status}
        difficulty={filters.difficulty}
        page={filters.page}
        onQChange={(value) => {
          filters.setPage(1);
          filters.setQ(value);
        }}
        onStatusChange={(value) => {
          filters.setPage(1);
          filters.setStatus(value);
        }}
        onDifficultyChange={(value) => {
          filters.setPage(1);
          filters.setDifficulty(value);
        }}
        onPrevious={() => filters.setPage(Math.max(1, filters.page - 1))}
        onNext={() => filters.setPage(filters.page + 1)}
      />

      {query.isLoading ? <LoadingState label="Loading courses" /> : null}
      {query.isError ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : null}
      {query.data ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {courses.length ? (
            courses.map((course) => (
              <CourseCard
                key={course.id}
                course={course}
                href={`/dashboard/student/courses/${course.id}`}
              />
            ))
          ) : (
            <div className="lg:col-span-2">
              <EmptyState message="No courses match the current filters or permissions." />
            </div>
          )}
        </div>
      ) : null}
    </PortalLayout>
  );
}

export function CourseDetailPage({ context }: { context: SessionContext }) {
  const { courseId = '' } = useParams();
  const query = useQuery({
    queryKey: ['courses', courseId],
    queryFn: () => getCourse(courseId),
    enabled: Boolean(courseId)
  });
  const structureQuery = useQuery({
    queryKey: ['courses', courseId, 'structure'],
    queryFn: () => getCourseStructure(courseId),
    enabled: Boolean(courseId)
  });
  const enrollMutation = useMutation({
    mutationFn: (course: Course) =>
      createEnrollment({
        student_profile_id: context.profile.id,
        course_id: course.id,
        institution_id: String(course.institution_id ?? context.profile.institution_id ?? ''),
        enrolled_by_profile_id: context.profile.id
      })
  });

  return (
    <PortalLayout context={context} activeNav="student-courses">
      {query.isLoading ? <LoadingState label="Loading course" /> : null}
      {query.isError ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : null}
      {query.data ? (
        <>
          <CourseDetailHeader
            course={query.data}
            actions={
              <>
                <Button
                  loading={enrollMutation.isPending}
                  loadingLabel="Enrolling"
                  onClick={() => enrollMutation.mutate(query.data)}
                >
                  Enroll
                </Button>
                <Link className={secondaryButtonClass} to={`/dashboard/student/courses/${query.data.id}/learn`}>
                  Start learning
                </Link>
              </>
            }
          />
          <PageHeader
            title="Course overview"
            description="Review metadata, outcomes, prerequisites, and course structure before learning."
            breadcrumbs={studentCourseBreadcrumbs(courseId, itemTitle(query.data))}
          >
            <div className="flex flex-wrap gap-2">
              <StatusBadge value={query.data.status} />
            </div>
          </PageHeader>
          {enrollMutation.isError ? <ErrorState title="Enrollment failed" error={enrollMutation.error} /> : null}
          {enrollMutation.data ? (
            <div className="mb-5 rounded border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
              Enrollment saved with status {String(enrollMutation.data.status ?? 'created')}.
            </div>
          ) : null}
          <div className="grid gap-4 xl:grid-cols-2">
            <Panel title="Metadata">
              <dl className="grid gap-2 text-sm text-slate-700">
                <div>Status: <StatusBadge value={query.data.status} /></div>
                <div>Difficulty: {query.data.difficulty_level || 'Not set'}</div>
                <div>Categories: {query.data.categories?.map((item) => itemTitle(item)).join(', ') || 'None'}</div>
                <div>Tags: {query.data.tags?.map((item) => itemTitle(item)).join(', ') || 'None'}</div>
                <div>Prerequisites: {query.data.prerequisite_course_ids?.join(', ') || 'None'}</div>
              </dl>
            </Panel>
            <Panel title="Learning outcomes">
              {query.data.learning_outcomes?.length ? (
                <ol className="list-decimal space-y-2 pl-5 text-sm text-slate-700">
                  {query.data.learning_outcomes.map((outcome) => (
                    <li key={outcome.id}>{String(outcome.description ?? itemTitle(outcome))}</li>
                  ))}
                </ol>
              ) : (
                <EmptyState message="No outcomes documented." />
              )}
            </Panel>
          </div>
          <div className="mt-4">
            {structureQuery.isLoading ? <LoadingState label="Loading course structure" /> : null}
            {structureQuery.isError ? <ErrorState error={structureQuery.error} onRetry={() => void structureQuery.refetch()} /> : null}
            {structureQuery.data ? (
              <Panel title="Modules and lessons">
                <CourseStructureTree structure={structureQuery.data} />
              </Panel>
            ) : null}
          </div>
        </>
      ) : null}
    </PortalLayout>
  );
}

export function StudentLearningPlayerPage({ context }: { context: SessionContext }) {
  const { courseId = '' } = useParams();
  const query = useQuery({
    queryKey: ['courses', courseId, 'structure'],
    queryFn: () => getCourseStructure(courseId),
    enabled: Boolean(courseId)
  });
  const firstModule = query.data?.modules?.[0];
  const firstLesson = firstModule?.lessons?.[0];
  const firstTopic = firstLesson?.topics?.[0];
  const assetId = firstTopic?.content_asset_id ?? firstLesson?.content_asset_id ?? null;
  const lessonMutation = useMutation({
    mutationFn: () =>
      updateLessonProgress({
        student_profile_id: context.profile.id,
        course_id: courseId,
        lesson_id: String(firstLesson?.id),
        status: 'completed',
        view_increment: 1,
        total_lessons: query.data?.modules?.flatMap((module) => module.lessons ?? []).length ?? 0
      })
  });
  const videoMutation = useMutation({
    mutationFn: () =>
      updateVideoProgress({
        student_profile_id: context.profile.id,
        course_id: courseId,
        content_asset_id: String(assetId),
        last_position_seconds: 600,
        duration_seconds: 600,
        percent_complete: 100
      })
  });
  const accessMutation = useMutation({
    mutationFn: () => createSignedAccess(String(assetId), context.profile.id)
  });

  return (
    <PortalLayout context={context} activeNav="student-courses">
      <PageHeader
        title="Learning Player"
        description="Read lesson content and update progress."
        breadcrumbs={studentCourseBreadcrumbs(courseId, query.data ? itemTitle(query.data) : undefined, 'Learn')}
      />
      {query.isLoading ? <LoadingState label="Loading lesson" /> : null}
      {query.isError ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : null}
      {query.data ? (
        <LessonPlayerLayout
          lessonTitle={firstLesson ? itemTitle(firstLesson) : 'No lesson selected'}
          summary={firstLesson?.summary}
          assetId={assetId}
          accessDenied={!firstLesson}
          actions={
            <>
              <Button onClick={() => lessonMutation.mutate()}>Mark lesson complete</Button>
              <Button
                variant="secondary"
                disabled={!assetId}
                disabledReason={!assetId ? 'Attach a content asset before marking video progress.' : undefined}
                onClick={() => videoMutation.mutate()}
              >
                Mark video complete
              </Button>
              <Button
                variant="secondary"
                disabled={!assetId}
                disabledReason={!assetId ? 'A signed access link needs an attached content asset.' : undefined}
                onClick={() => accessMutation.mutate()}
              >
                Request access link
              </Button>
              {lessonMutation.isError ? <ErrorState title="Lesson progress failed" error={lessonMutation.error} /> : null}
              {videoMutation.isError ? <ErrorState title="Video progress failed" error={videoMutation.error} /> : null}
              {accessMutation.isError ? <ErrorState title="Access denied" error={accessMutation.error} /> : null}
              {accessMutation.data ? <JsonPreview value={accessMutation.data} /> : null}
            </>
          }
          outline={<CourseStructureTree structure={query.data} />}
        />
      ) : null}
    </PortalLayout>
  );
}

function assignedCourseIds(context: SessionContext) {
  return Array.from(
    new Set(
      context.session.role_assignments
        .filter((assignment) => assignment.scope_type === 'course' && assignment.scope_id)
        .map((assignment) => String(assignment.scope_id))
    )
  );
}

function instructorBreadcrumbs(items: Array<{ label: string; href?: string }> = []) {
  return [{ label: 'Instructor', href: '/dashboard/instructor' }, ...items];
}

function courseBreadcrumbs(courseId: string, title?: string, tail?: string) {
  return instructorBreadcrumbs([
    { label: 'Courses', href: '/dashboard/instructor/courses' },
    {
      label: title || 'Course',
      href: tail ? `/dashboard/instructor/courses/${courseId}` : undefined
    },
    ...(tail ? [{ label: tail }] : [])
  ]);
}

function courseWorkspaceLinkClass(active: boolean) {
  return `block rounded-control px-3 py-2 text-sm font-medium ${
    active ? 'bg-emerald-50 text-emerald-800' : 'text-slate-700 hover:bg-slate-100'
  }`;
}

function CourseWorkspaceShell({
  courseId,
  activeTab,
  children
}: {
  courseId: string;
  activeTab: 'overview' | 'builder' | 'question-banks' | 'participants' | 'assessments';
  children: ReactNode;
}) {
  return (
    <div className="grid gap-5 xl:grid-cols-[180px_1fr]">
      <nav
        aria-label="Course"
        className="h-fit rounded-panel border border-slate-200 bg-white p-3 shadow-panel"
      >
        <div className="mb-3 px-2 text-xs font-semibold uppercase text-slate-500">
          Course
        </div>
        <Link
          className={courseWorkspaceLinkClass(activeTab === 'overview')}
          to={`/dashboard/instructor/courses/${courseId}`}
        >
          Overview
        </Link>
        <Link
          className={courseWorkspaceLinkClass(activeTab === 'builder')}
          to={`/dashboard/instructor/courses/${courseId}/builder`}
        >
          Builder
        </Link>
        <Link
          className={courseWorkspaceLinkClass(activeTab === 'question-banks')}
          to={`/dashboard/instructor/courses/${courseId}/question-banks`}
        >
          Question banks
        </Link>
        <Link
          className={courseWorkspaceLinkClass(activeTab === 'participants')}
          to={`/dashboard/instructor/courses/${courseId}/participants`}
        >
          Participants
        </Link>
        <Link
          className={courseWorkspaceLinkClass(activeTab === 'assessments')}
          to={`/dashboard/instructor/courses/${courseId}/assessments`}
        >
          Assessments
        </Link>
      </nav>
      <div>{children}</div>
    </div>
  );
}

function staffRoleLabel(roleCode: string) {
  if (roleCode === 'teaching_assistant') {
    return 'Teaching Assistant';
  }
  if (roleCode === 'instructor') {
    return 'Instructor';
  }
  return roleCode.replaceAll('_', ' ');
}

function courseAccessRequired(
  context: SessionContext,
  courseId: string,
  title: string,
  tail?: string
) {
  return (
    <PortalLayout context={context} activeNav="instructor-courses" hidePortalNav>
      <PageHeader title={title} breadcrumbs={courseBreadcrumbs(courseId || 'unassigned', undefined, tail)}>
        <Link className={secondaryButtonClass} to="/dashboard/instructor/courses">
          Back to courses
        </Link>
      </PageHeader>
      <ErrorState
        title="Course access required"
        error={new Error('This instructor account is not assigned to the requested course.')}
      />
    </PortalLayout>
  );
}

type StructureItemType = 'module' | 'lesson' | 'topic';

type StructureFormValues = {
  action: StructureItemType;
  module_id: string;
  lesson_id: string;
  title: string;
  position: string;
  content_asset_id: string;
  description: string;
};

function emptyStructureForm(): StructureFormValues {
  return {
    action: 'module',
    module_id: '',
    lesson_id: '',
    title: '',
    position: '1',
    content_asset_id: '',
    description: ''
  };
}

export function InstructorCourseManagementPage({ context }: { context: SessionContext }) {
  const courseIds = useMemo(() => assignedCourseIds(context), [context]);
  const query = useQuery({
    queryKey: ['courses', 'instructor-assigned', courseIds],
    queryFn: () => Promise.all(courseIds.map((courseId) => getCourse(courseId))),
    enabled: courseIds.length > 0
  });
  const courses = query.data ?? [];

  return (
    <PortalLayout context={context} activeNav="instructor-courses">
      <PageHeader
        title="Course Management"
        description="Open courses assigned to your instructor role."
        breadcrumbs={instructorBreadcrumbs([{ label: 'Courses' }])}
      />
      <Panel title="Your courses">
        {!courseIds.length ? <EmptyState message="No courses are assigned to your instructor role." /> : null}
        {query.isLoading ? <LoadingState label="Loading assigned courses" /> : null}
        {query.isError ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : null}
        {query.data && !courses.length ? <EmptyState message="No assigned courses could be loaded." /> : null}
        {courses.length ? (
          <div className="overflow-x-auto rounded-panel border border-slate-200 bg-white">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <caption className="sr-only">Assigned courses</caption>
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3" scope="col">Title</th>
                  <th className="px-4 py-3" scope="col">Difficulty</th>
                  <th className="px-4 py-3" scope="col">Status</th>
                  <th className="px-4 py-3" scope="col">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {courses.map((course) => (
                  <tr key={course.id}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-950">{itemTitle(course)}</div>
                      <div className="mt-1 text-xs text-slate-500">{course.slug || 'No slug'}</div>
                    </td>
                    <td className="px-4 py-3 text-slate-700">
                      {course.difficulty_level || 'None'}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge value={course.status} />
                    </td>
                    <td className="px-4 py-3">
                      <Link className={secondaryButtonClass} to={`/dashboard/instructor/courses/${course.id}`}>
                        Open
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </Panel>
    </PortalLayout>
  );
}

export function InstructorCourseWorkspacePage({ context }: { context: SessionContext }) {
  const { courseId = '' } = useParams();
  const courseIds = useMemo(() => assignedCourseIds(context), [context]);
  const canOpenCourse = Boolean(courseId && courseIds.includes(courseId));
  const courseQuery = useQuery({
    queryKey: ['courses', courseId],
    queryFn: () => getCourse(courseId),
    enabled: canOpenCourse
  });

  if (!canOpenCourse) {
    return (
      <PortalLayout context={context} activeNav="instructor-courses" hidePortalNav>
        <PageHeader
          title="Course overview"
          breadcrumbs={courseBreadcrumbs(courseId || 'unassigned')}
        >
          <Link className={secondaryButtonClass} to="/dashboard/instructor/courses">
            Back to courses
          </Link>
        </PageHeader>
        <ErrorState
          title="Course access required"
          error={new Error('This instructor account is not assigned to the requested course.')}
        />
      </PortalLayout>
    );
  }

  const courseTitle = courseQuery.data ? itemTitle(courseQuery.data) : 'Course';

  return (
    <PortalLayout context={context} activeNav="instructor-courses" hidePortalNav>
      <PageHeader
        title="Course overview"
        description="Review course details and open authoring tools for this assigned course."
        breadcrumbs={courseBreadcrumbs(courseId, courseTitle)}
      >
        <Link className={secondaryButtonClass} to="/dashboard/instructor/courses">
          Back to courses
        </Link>
      </PageHeader>
      <CourseWorkspaceShell courseId={courseId} activeTab="overview">
        {courseQuery.isLoading ? <LoadingState label="Loading course" /> : null}
        {courseQuery.isError ? (
          <ErrorState error={courseQuery.error} onRetry={() => void courseQuery.refetch()} />
        ) : null}
        {courseQuery.data ? (
          <div className="space-y-5">
            <CourseDetailHeader
              course={courseQuery.data}
              actions={
                <Link
                  className={secondaryButtonClass}
                  to={`/dashboard/instructor/courses/${courseQuery.data.id}/builder`}
                >
                  Open builder
                </Link>
              }
            />
            <div className="grid gap-4 xl:grid-cols-2">
              <Panel title="Metadata">
                <dl className="grid gap-2 text-sm text-slate-700">
                  <div>Status: <StatusBadge value={courseQuery.data.status} /></div>
                  <div>Difficulty: {courseQuery.data.difficulty_level || 'Not set'}</div>
                  <div>Categories: {courseQuery.data.categories?.map((item) => itemTitle(item)).join(', ') || 'None'}</div>
                  <div>Tags: {courseQuery.data.tags?.map((item) => itemTitle(item)).join(', ') || 'None'}</div>
                  <div>Prerequisites: {courseQuery.data.prerequisite_course_ids?.join(', ') || 'None'}</div>
                </dl>
              </Panel>
              <Panel title="Learning outcomes">
                {courseQuery.data.learning_outcomes?.length ? (
                  <ol className="list-decimal space-y-2 pl-5 text-sm text-slate-700">
                    {courseQuery.data.learning_outcomes.map((outcome) => (
                      <li key={outcome.id}>
                        {String(outcome.description ?? itemTitle(outcome))}
                      </li>
                    ))}
                  </ol>
                ) : (
                  <EmptyState message="No outcomes documented." />
                )}
              </Panel>
            </div>
          </div>
        ) : null}
      </CourseWorkspaceShell>
    </PortalLayout>
  );
}

export function CourseBuilderPage({ context }: { context: SessionContext }) {
  const { courseId = '' } = useParams();
  const queryClient = useQueryClient();
  const courseIds = useMemo(() => assignedCourseIds(context), [context]);
  const canOpenCourse = Boolean(courseId && courseIds.includes(courseId));
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isAddStructureOpen, setIsAddStructureOpen] = useState(false);
  const [structureForm, setStructureForm] = useState<StructureFormValues>(emptyStructureForm);
  useUnsavedChangesWarning(hasUnsavedChanges, 'Course builder has unsaved module, lesson, or topic changes.');
  const query = useQuery({
    queryKey: ['courses', courseId, 'structure'],
    queryFn: () => getCourseStructure(courseId),
    enabled: Boolean(courseId && canOpenCourse)
  });
  const mutation = useMutation({
    mutationFn: async (values: StructureFormValues) => {
      const position = Number(values.position || 1);
      if (values.action === 'module') {
        return createModule(courseId, {
          title: values.title.trim(),
          description: values.description.trim() || null,
          position
        });
      }
      if (values.action === 'lesson') {
        return createLesson(values.module_id, {
          title: values.title.trim(),
          summary: values.description.trim() || null,
          position,
          content_asset_id: values.content_asset_id.trim() || null
        });
      }
      return createTopic(values.lesson_id, {
        title: values.title.trim(),
        position,
        content_asset_id: values.content_asset_id.trim() || null
      });
    },
    onSuccess: async () => {
      setHasUnsavedChanges(false);
      setStructureForm(emptyStructureForm());
      setIsAddStructureOpen(false);
      await queryClient.invalidateQueries({ queryKey: ['courses', courseId, 'structure'] });
    }
  });
  const publishLessonMutation = useMutation({
    mutationFn: publishLesson,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['courses', courseId, 'structure'] });
    }
  });
  const modules = query.data?.modules ?? [];
  const lessonOptions = modules.flatMap((module) =>
    (module.lessons ?? []).map((lesson) => ({
      lesson,
      label: `${itemTitle(module)} / ${itemTitle(lesson)}`
    }))
  );
  const canSaveStructure = Boolean(
    structureForm.title.trim() &&
      (structureForm.action !== 'lesson' || structureForm.module_id) &&
      (structureForm.action !== 'topic' || structureForm.lesson_id)
  );

  function updateStructureForm(values: Partial<StructureFormValues>) {
    setHasUnsavedChanges(true);
    setStructureForm((current) => ({ ...current, ...values }));
    mutation.reset();
  }

  function setStructureType(action: StructureItemType) {
    updateStructureForm({
      action,
      module_id: '',
      lesson_id: '',
      content_asset_id: '',
      description: ''
    });
  }

  function closeAddStructure() {
    setIsAddStructureOpen(false);
    setStructureForm(emptyStructureForm());
    setHasUnsavedChanges(false);
    mutation.reset();
  }

  function submitStructureForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (canSaveStructure) {
      mutation.mutate(structureForm);
    }
  }

  if (!canOpenCourse) {
    return (
      <PortalLayout context={context} activeNav="instructor-courses" hidePortalNav>
        <PageHeader
          title="Course Builder"
          breadcrumbs={courseBreadcrumbs(courseId || 'unassigned', undefined, 'Builder')}
        >
          <Link className={secondaryButtonClass} to="/dashboard/instructor/courses">
            Back to courses
          </Link>
        </PageHeader>
        <ErrorState
          title="Course access required"
          error={new Error('This instructor account is not assigned to the requested course.')}
        />
      </PortalLayout>
    );
  }

  const courseTitle = query.data ? itemTitle(query.data) : 'Course';

  return (
    <PortalLayout context={context} activeNav="instructor-courses" hidePortalNav>
      <PageHeader
        title="Course Builder"
        description="Author modules, lessons, topics, ordering, and content attachments."
        breadcrumbs={courseBreadcrumbs(courseId, courseTitle, 'Builder')}
      >
        <Button type="button" onClick={() => setIsAddStructureOpen(true)} disabled={!query.data}>
          Add structure
        </Button>
        <Link className={secondaryButtonClass} to={`/dashboard/instructor/courses/${courseId}/assessments`}>
          Manage assessments
        </Link>
        <Link className={secondaryButtonClass} to="/dashboard/instructor/courses">
          Back to courses
        </Link>
      </PageHeader>
      <CourseWorkspaceShell courseId={courseId} activeTab="builder">
        {query.isLoading ? <LoadingState label="Loading structure" /> : null}
        {query.isError ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : null}
        {query.data ? (
          <Panel title={itemTitle(query.data)}>
            <CourseStructureTree
              structure={query.data}
              mode="author"
              onPublishLesson={(lessonId) => publishLessonMutation.mutate(lessonId)}
            />
          </Panel>
        ) : null}
      </CourseWorkspaceShell>
      <Modal title="Add structure" open={isAddStructureOpen} onClose={closeAddStructure}>
        <form className="space-y-4" onSubmit={submitStructureForm}>
          <Field htmlFor="builder-action" label="Item type" required>
            <select
              id="builder-action"
              className={fieldClass}
              value={structureForm.action}
              onChange={(event) => setStructureType(event.target.value as StructureItemType)}
            >
              <option value="module">Module</option>
              <option value="lesson">Lesson</option>
              <option value="topic">Topic</option>
            </select>
          </Field>
          {structureForm.action === 'lesson' ? (
            <Field htmlFor="builder-module" label="Module" required>
              <select
                id="builder-module"
                className={fieldClass}
                disabled={!modules.length}
                value={structureForm.module_id}
                onChange={(event) => updateStructureForm({ module_id: event.target.value })}
              >
                <option value="">Select module</option>
                {modules.map((module) => (
                  <option key={module.id} value={module.id}>
                    {itemTitle(module)}
                  </option>
                ))}
              </select>
            </Field>
          ) : null}
          {structureForm.action === 'topic' ? (
            <Field htmlFor="builder-lesson" label="Lesson" required>
              <select
                id="builder-lesson"
                className={fieldClass}
                disabled={!lessonOptions.length}
                value={structureForm.lesson_id}
                onChange={(event) => updateStructureForm({ lesson_id: event.target.value })}
              >
                <option value="">Select lesson</option>
                {lessonOptions.map(({ lesson, label }) => (
                  <option key={lesson.id} value={lesson.id}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
          ) : null}
          <Field htmlFor="builder-title" label="Title" required>
            <input
              id="builder-title"
              className={fieldClass}
              required
              value={structureForm.title}
              onChange={(event) => updateStructureForm({ title: event.target.value })}
            />
          </Field>
          <Field htmlFor="builder-position" label="Position">
            <input
              id="builder-position"
              className={fieldClass}
              min={1}
              type="number"
              value={structureForm.position}
              onChange={(event) => updateStructureForm({ position: event.target.value })}
            />
          </Field>
          {structureForm.action !== 'module' ? (
            <Field htmlFor="builder-asset" label="Content asset">
              <input
                id="builder-asset"
                className={fieldClass}
                placeholder="Optional content asset reference"
                value={structureForm.content_asset_id}
                onChange={(event) => updateStructureForm({ content_asset_id: event.target.value })}
              />
            </Field>
          ) : null}
          {structureForm.action !== 'topic' ? (
            <Field
              htmlFor="builder-description"
              label={structureForm.action === 'module' ? 'Description' : 'Summary'}
            >
              <textarea
                id="builder-description"
                className={fieldClass}
                rows={3}
                value={structureForm.description}
                onChange={(event) => updateStructureForm({ description: event.target.value })}
              />
            </Field>
          ) : null}
          {structureForm.action === 'lesson' && !modules.length ? (
            <EmptyState message="Create a module before adding lessons." />
          ) : null}
          {structureForm.action === 'topic' && !lessonOptions.length ? (
            <EmptyState message="Create a lesson before adding topics." />
          ) : null}
          {mutation.isError ? <ErrorState title="Save failed" error={mutation.error} /> : null}
          <div className="flex flex-wrap justify-end gap-2">
            <Button type="button" variant="secondary" onClick={closeAddStructure}>
              Cancel
            </Button>
            <Button type="submit" loading={mutation.isPending} loadingLabel="Saving" disabled={!canSaveStructure}>
              Save item
            </Button>
          </div>
        </form>
      </Modal>
    </PortalLayout>
  );
}

export function InstructorCourseQuestionBanksPage({ context }: { context: SessionContext }) {
  const { courseId = '' } = useParams();
  const queryClient = useQueryClient();
  const courseIds = useMemo(() => assignedCourseIds(context), [context]);
  const canOpenCourse = Boolean(courseId && courseIds.includes(courseId));
  const [selectedBankId, setSelectedBankId] = useState('');
  const [questionType, setQuestionType] = useState('multiple_choice');

  const courseQuery = useQuery({
    queryKey: ['courses', courseId],
    queryFn: () => getCourse(courseId),
    enabled: canOpenCourse
  });
  const institutionId = String(courseQuery.data?.institution_id ?? '');
  const banksQuery = useQuery({
    queryKey: ['course-question-banks', courseId, institutionId, context.profile.id],
    queryFn: () =>
      listQuestionBanks({
        institution_id: institutionId,
        owner_profile_id: context.profile.id,
        page_size: 100,
        sort: '-created_at'
      }),
    enabled: canOpenCourse && Boolean(institutionId)
  });
  const banks = toList(banksQuery.data);
  const questionsQuery = useQuery({
    queryKey: ['course-question-bank-questions', selectedBankId],
    queryFn: () => listQuestions(selectedBankId, { page_size: 100, sort: '-created_at' }),
    enabled: canOpenCourse && Boolean(selectedBankId)
  });
  const questions = toList(questionsQuery.data);
  const invalidateBanks = async () => {
    await queryClient.invalidateQueries({ queryKey: ['course-question-banks', courseId] });
  };
  const bankMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return createQuestionBank({
        institution_id: institutionId,
        owner_profile_id: context.profile.id,
        title: String(data.get('title') || ''),
        description: String(data.get('description') || '') || null
      });
    },
    onSuccess: async (bank) => {
      setSelectedBankId(bank.id);
      await invalidateBanks();
    }
  });
  const questionMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      const choices = parseCsv(String(data.get('choices') || 'A, B')).map((choice, index) => ({
        id: String.fromCharCode(65 + index),
        text: choice
      }));
      return createQuestion(String(data.get('question_bank_id') || selectedBankId), {
        question_type: questionType,
        prompt: String(data.get('prompt') || ''),
        choices: questionType === 'multiple_choice' ? choices : undefined,
        correct_answer:
          questionType === 'multiple_choice'
            ? { choice_id: choices[0]?.id ?? 'A' }
            : { value: true },
        points: Number(data.get('points') || 1),
        status: 'draft'
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['course-question-bank-questions', selectedBankId] });
    }
  });

  if (!canOpenCourse) {
    return courseAccessRequired(context, courseId, 'Question banks', 'Question banks');
  }

  const courseTitle = courseQuery.data ? itemTitle(courseQuery.data) : 'Course';

  return (
    <PortalLayout context={context} activeNav="instructor-courses" hidePortalNav>
      <PageHeader
        title="Question banks"
        description="Create course-context question banks and questions owned by your instructor profile."
        breadcrumbs={courseBreadcrumbs(courseId, courseTitle, 'Question banks')}
      >
        <Link className={secondaryButtonClass} to={`/dashboard/instructor/courses/${courseId}/builder`}>
          Back to builder
        </Link>
      </PageHeader>
      <CourseWorkspaceShell courseId={courseId} activeTab="question-banks">
        {courseQuery.isLoading ? <LoadingState label="Loading course" /> : null}
        {courseQuery.isError ? <ErrorState error={courseQuery.error} onRetry={() => void courseQuery.refetch()} /> : null}
        {courseQuery.data ? (
          <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
            <div className="space-y-5">
              <Panel title="New bank">
                <form
                  className="space-y-4"
                  onSubmit={(event) => {
                    event.preventDefault();
                    bankMutation.mutate(event.currentTarget);
                  }}
                >
                  <Field htmlFor="course-bank-title" label="Title" required>
                    <input id="course-bank-title" name="title" className={fieldClass} required />
                  </Field>
                  <Field htmlFor="course-bank-description" label="Description">
                    <textarea id="course-bank-description" name="description" className={fieldClass} rows={3} />
                  </Field>
                  {bankMutation.isError ? <ErrorState title="Bank save failed" error={bankMutation.error} /> : null}
                  <Button type="submit" loading={bankMutation.isPending} loadingLabel="Saving">
                    Create bank
                  </Button>
                </form>
              </Panel>
              <Panel title="New question">
                <form
                  className="space-y-4"
                  onSubmit={(event) => {
                    event.preventDefault();
                    questionMutation.mutate(event.currentTarget);
                  }}
                >
                  <Field htmlFor="course-question-bank" label="Question bank" required>
                    <select
                      id="course-question-bank"
                      name="question_bank_id"
                      className={fieldClass}
                      required
                      value={selectedBankId}
                      onChange={(event) => setSelectedBankId(event.target.value)}
                    >
                      <option value="">Select bank</option>
                      {banks.map((bank) => (
                        <option key={bank.id} value={bank.id}>
                          {itemTitle(bank)}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field htmlFor="course-question-type" label="Question type">
                    <select
                      id="course-question-type"
                      name="question_type"
                      className={fieldClass}
                      value={questionType}
                      onChange={(event) => setQuestionType(event.target.value)}
                    >
                      <option value="multiple_choice">Multiple choice</option>
                      <option value="true_false">True/false</option>
                      <option value="short_answer">Short answer</option>
                      <option value="essay">Essay</option>
                    </select>
                  </Field>
                  <Field htmlFor="course-question-prompt" label="Prompt" required>
                    <textarea id="course-question-prompt" name="prompt" className={fieldClass} rows={4} required />
                  </Field>
                  {questionType === 'multiple_choice' ? (
                    <Field htmlFor="course-question-choices" label="Choices">
                      <input
                        id="course-question-choices"
                        name="choices"
                        className={fieldClass}
                        defaultValue="Choice A, Choice B"
                      />
                    </Field>
                  ) : null}
                  <Field htmlFor="course-question-points" label="Points">
                    <input id="course-question-points" name="points" className={fieldClass} type="number" min={0} defaultValue={1} />
                  </Field>
                  {questionMutation.isError ? <ErrorState title="Question save failed" error={questionMutation.error} /> : null}
                  <Button
                    type="submit"
                    loading={questionMutation.isPending}
                    loadingLabel="Saving"
                    disabled={!selectedBankId}
                  >
                    Create question
                  </Button>
                </form>
              </Panel>
            </div>
            <div className="space-y-5">
              <Panel title="Banks">
                {banksQuery.isLoading ? <LoadingState label="Loading banks" /> : null}
                {banksQuery.isError ? <ErrorState error={banksQuery.error} onRetry={() => void banksQuery.refetch()} /> : null}
                {banks.length ? (
                  <ul className="divide-y divide-slate-100">
                    {banks.map((bank) => (
                      <li className="flex flex-wrap items-center justify-between gap-3 py-3" key={bank.id}>
                        <div>
                          <div className="font-medium text-slate-950">{itemTitle(bank)}</div>
                          <div className="mt-1 text-xs text-slate-500">{String(bank.description ?? 'No description')}</div>
                        </div>
                        <Button variant="secondary" size="sm" onClick={() => setSelectedBankId(bank.id)}>
                          Select
                        </Button>
                      </li>
                    ))}
                  </ul>
                ) : banksQuery.data ? (
                  <EmptyState message="No question banks yet." />
                ) : null}
              </Panel>
              <Panel title="Questions">
                {!selectedBankId ? <EmptyState message="Select a question bank by title to view questions." /> : null}
                {questionsQuery.isLoading ? <LoadingState label="Loading questions" /> : null}
                {questionsQuery.isError ? <ErrorState error={questionsQuery.error} onRetry={() => void questionsQuery.refetch()} /> : null}
                {questions.length ? (
                  <ul className="divide-y divide-slate-100">
                    {questions.map((question) => (
                      <li className="py-3" key={question.id}>
                        <div className="font-medium text-slate-950">{question.prompt || itemTitle(question)}</div>
                        <div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-500">
                          <span>{question.question_type || 'question'}</span>
                          <span>{question.points ?? 0} points</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : selectedBankId && questionsQuery.data ? (
                  <EmptyState message="No questions in this bank yet." />
                ) : null}
              </Panel>
            </div>
          </div>
        ) : null}
      </CourseWorkspaceShell>
    </PortalLayout>
  );
}

export function InstructorCourseParticipantsPage({ context }: { context: SessionContext }) {
  const { courseId = '' } = useParams();
  const courseIds = useMemo(() => assignedCourseIds(context), [context]);
  const canOpenCourse = Boolean(courseId && courseIds.includes(courseId));
  const courseQuery = useQuery({
    queryKey: ['courses', courseId],
    queryFn: () => getCourse(courseId),
    enabled: canOpenCourse
  });
  const enrollmentsQuery = useQuery({
    queryKey: ['course-participants', courseId, 'enrollments'],
    queryFn: () => listEnrollments({ course_id: courseId, page_size: 100, sort: '-created_at' }),
    enabled: canOpenCourse
  });
  const staffQuery = useQuery({
    queryKey: ['course-participants', courseId, 'staff'],
    queryFn: () =>
      listRoleAssignments({
        scope_type: 'course',
        scope_id: courseId,
        role_code: 'instructor,teaching_assistant'
      }),
    enabled: canOpenCourse
  });
  const enrollments = toList(enrollmentsQuery.data) as Enrollment[];
  const staff = staffQuery.data ?? [];

  if (!canOpenCourse) {
    return courseAccessRequired(context, courseId, 'Participants', 'Participants');
  }

  const courseTitle = courseQuery.data ? itemTitle(courseQuery.data) : 'Course';

  return (
    <PortalLayout context={context} activeNav="instructor-courses" hidePortalNav>
      <PageHeader
        title="Participants"
        description="Review enrolled students and course staff assignments."
        breadcrumbs={courseBreadcrumbs(courseId, courseTitle, 'Participants')}
      >
        <Link className={secondaryButtonClass} to={`/dashboard/instructor/courses/${courseId}/builder`}>
          Back to builder
        </Link>
      </PageHeader>
      <CourseWorkspaceShell courseId={courseId} activeTab="participants">
        {courseQuery.isLoading ? <LoadingState label="Loading course" /> : null}
        {courseQuery.isError ? <ErrorState error={courseQuery.error} onRetry={() => void courseQuery.refetch()} /> : null}
        {courseQuery.data ? (
          <div className="grid gap-5 xl:grid-cols-2">
            <Panel title="Students" actions={<span className="text-sm text-slate-500">{enrollments.length} total</span>}>
              {enrollmentsQuery.isLoading ? <LoadingState label="Loading enrollments" /> : null}
              {enrollmentsQuery.isError ? <ErrorState error={enrollmentsQuery.error} onRetry={() => void enrollmentsQuery.refetch()} /> : null}
              {enrollments.length ? (
                <ul className="divide-y divide-slate-100">
                  {enrollments.map((enrollment) => (
                    <li className="py-3" key={enrollment.id}>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium text-slate-950">
                          {enrollment.student_profile_id || enrollment.id}
                        </span>
                        <StatusBadge value={enrollment.status ?? null} />
                      </div>
                      <div className="mt-1 text-xs text-slate-500">
                        Enrolled {enrollment.enrolled_at || enrollment.created_at || 'date unavailable'}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : enrollmentsQuery.data ? (
                <EmptyState message="No enrolled students found." />
              ) : null}
            </Panel>
            <Panel title="Course staff" actions={<span className="text-sm text-slate-500">{staff.length} total</span>}>
              {staffQuery.isLoading ? <LoadingState label="Loading staff assignments" /> : null}
              {staffQuery.isError ? <ErrorState error={staffQuery.error} onRetry={() => void staffQuery.refetch()} /> : null}
              {staff.length ? (
                <ul className="divide-y divide-slate-100">
                  {staff.map((assignment: RoleAssignment) => (
                    <li className="py-3" key={assignment.id}>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium text-slate-950">
                          {assignment.account_id || assignment.id}
                        </span>
                        <StatusBadge value={staffRoleLabel(assignment.role_code)} />
                      </div>
                      <div className="mt-1 text-xs text-slate-500">
                        Assigned {assignment.assigned_at || 'date unavailable'}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : staffQuery.data ? (
                <EmptyState message="No course staff assignments found." />
              ) : null}
            </Panel>
          </div>
        ) : null}
      </CourseWorkspaceShell>
    </PortalLayout>
  );
}

type AssessmentFormValues = {
  id: string;
  title: string;
  assessment_type: string;
  instructions: string;
  max_attempts: string;
  max_points: string;
  available_from: string;
  available_until: string;
};

const emptyAssessmentForm: AssessmentFormValues = {
  id: '',
  title: '',
  assessment_type: 'quiz',
  instructions: '',
  max_attempts: '1',
  max_points: '100',
  available_from: '',
  available_until: ''
};

function toAssessmentForm(assessment: Assessment): AssessmentFormValues {
  return {
    id: assessment.id,
    title: itemTitle(assessment),
    assessment_type: assessment.assessment_type || 'quiz',
    instructions: assessment.instructions || '',
    max_attempts: String((assessment.quiz as Record<string, unknown> | undefined)?.max_attempts ?? 1),
    max_points: String((assessment.assignment as Record<string, unknown> | undefined)?.max_points ?? 100),
    available_from: assessment.available_from || '',
    available_until: assessment.available_until || ''
  };
}

export function InstructorCourseAssessmentsPage({ context }: { context: SessionContext }) {
  const { courseId = '' } = useParams();
  const queryClient = useQueryClient();
  const courseIds = useMemo(() => assignedCourseIds(context), [context]);
  const canOpenCourse = Boolean(courseId && courseIds.includes(courseId));
  const [formValues, setFormValues] = useState<AssessmentFormValues>(emptyAssessmentForm);
  const [attachAssessmentId, setAttachAssessmentId] = useState('');
  const [attachBankId, setAttachBankId] = useState('');
  const [selectedQuestionIds, setSelectedQuestionIds] = useState<string[]>([]);

  const courseQuery = useQuery({
    queryKey: ['courses', courseId],
    queryFn: () => getCourse(courseId),
    enabled: canOpenCourse
  });
  const institutionId = String(courseQuery.data?.institution_id ?? '');
  const assessmentsQuery = useQuery({
    queryKey: ['course-assessments', courseId],
    queryFn: () => listAssessments({ course_id: courseId, page_size: 100, sort: '-created_at' }),
    enabled: canOpenCourse
  });
  const banksQuery = useQuery({
    queryKey: ['course-assessment-banks', courseId, institutionId, context.profile.id],
    queryFn: () =>
      listQuestionBanks({
        institution_id: institutionId,
        owner_profile_id: context.profile.id,
        page_size: 100,
        sort: '-created_at'
      }),
    enabled: canOpenCourse && Boolean(institutionId)
  });
  const questionsQuery = useQuery({
    queryKey: ['course-assessment-bank-questions', attachBankId],
    queryFn: () => listQuestions(attachBankId, { page_size: 100, sort: '-created_at' }),
    enabled: canOpenCourse && Boolean(attachBankId)
  });
  const assessments = toList(assessmentsQuery.data) as Assessment[];
  const banks = toList(banksQuery.data);
  const questions = toList(questionsQuery.data);
  const invalidateAssessments = async () => {
    await queryClient.invalidateQueries({ queryKey: ['course-assessments', courseId] });
  };
  const saveAssessmentMutation = useMutation({
    mutationFn: () => {
      const basePayload = {
        title: formValues.title.trim(),
        instructions: formValues.instructions.trim() || null,
        available_from: formValues.available_from || null,
        available_until: formValues.available_until || null
      };
      if (formValues.id) {
        return updateAssessment(formValues.id, basePayload);
      }
      return createAssessment({
        ...basePayload,
        course_id: courseId,
        institution_id: institutionId,
        owner_profile_id: context.profile.id,
        assessment_type: formValues.assessment_type,
        quiz:
          formValues.assessment_type === 'quiz' || formValues.assessment_type === 'exam'
            ? { max_attempts: Number(formValues.max_attempts || 1), randomize_questions: false }
            : undefined,
        assignment:
          formValues.assessment_type === 'assignment'
            ? { max_points: Number(formValues.max_points || 100), allow_late_submission: true }
            : undefined
      });
    },
    onSuccess: async () => {
      setFormValues(emptyAssessmentForm);
      await invalidateAssessments();
    }
  });
  const attachMutation = useMutation({
    mutationFn: () =>
      replaceAssessmentQuestions(
        attachAssessmentId,
        selectedQuestionIds.map((questionId, index) => ({ question_id: questionId, position: index + 1 }))
      ),
    onSuccess: async () => {
      setSelectedQuestionIds([]);
      await invalidateAssessments();
    }
  });
  const lifecycleMutation = useMutation({
    mutationFn: ({ assessmentId, action }: { assessmentId: string; action: 'publish' | 'close' }) =>
      action === 'publish' ? publishAssessment(assessmentId) : closeAssessment(assessmentId),
    onSuccess: invalidateAssessments
  });

  function updateAssessmentForm(values: Partial<AssessmentFormValues>) {
    setFormValues((current) => ({ ...current, ...values }));
  }

  if (!canOpenCourse) {
    return courseAccessRequired(context, courseId, 'Assessments', 'Assessments');
  }

  const courseTitle = courseQuery.data ? itemTitle(courseQuery.data) : 'Course';

  return (
    <PortalLayout context={context} activeNav="instructor-courses" hidePortalNav>
      <PageHeader
        title="Assessments"
        description="Create, edit, attach questions, publish, and close assessments for this course."
        breadcrumbs={courseBreadcrumbs(courseId, courseTitle, 'Assessments')}
      >
        <Link className={secondaryButtonClass} to={`/dashboard/instructor/courses/${courseId}/builder`}>
          Back to builder
        </Link>
      </PageHeader>
      <CourseWorkspaceShell courseId={courseId} activeTab="assessments">
        {courseQuery.isLoading ? <LoadingState label="Loading course" /> : null}
        {courseQuery.isError ? <ErrorState error={courseQuery.error} onRetry={() => void courseQuery.refetch()} /> : null}
        {courseQuery.data ? (
          <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
            <div className="space-y-5">
              <Panel title={formValues.id ? 'Edit assessment' : 'New assessment'}>
                <form
                  className="space-y-4"
                  onSubmit={(event) => {
                    event.preventDefault();
                    saveAssessmentMutation.mutate();
                  }}
                >
                  <Field htmlFor="course-assessment-title" label="Title" required>
                    <input
                      id="course-assessment-title"
                      className={fieldClass}
                      required
                      value={formValues.title}
                      onChange={(event) => updateAssessmentForm({ title: event.target.value })}
                    />
                  </Field>
                  <Field htmlFor="course-assessment-type" label="Type">
                    <select
                      id="course-assessment-type"
                      className={fieldClass}
                      disabled={Boolean(formValues.id)}
                      value={formValues.assessment_type}
                      onChange={(event) => updateAssessmentForm({ assessment_type: event.target.value })}
                    >
                      <option value="quiz">Quiz</option>
                      <option value="exam">Exam</option>
                      <option value="assignment">Assignment</option>
                    </select>
                  </Field>
                  <Field htmlFor="course-assessment-instructions" label="Instructions">
                    <textarea
                      id="course-assessment-instructions"
                      className={fieldClass}
                      rows={3}
                      value={formValues.instructions}
                      onChange={(event) => updateAssessmentForm({ instructions: event.target.value })}
                    />
                  </Field>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Field htmlFor="course-assessment-start" label="Available from">
                      <input
                        id="course-assessment-start"
                        className={fieldClass}
                        type="datetime-local"
                        value={formValues.available_from}
                        onChange={(event) => updateAssessmentForm({ available_from: event.target.value })}
                      />
                    </Field>
                    <Field htmlFor="course-assessment-end" label="Available until">
                      <input
                        id="course-assessment-end"
                        className={fieldClass}
                        type="datetime-local"
                        value={formValues.available_until}
                        onChange={(event) => updateAssessmentForm({ available_until: event.target.value })}
                      />
                    </Field>
                  </div>
                  {formValues.assessment_type === 'assignment' ? (
                    <Field htmlFor="course-assessment-points" label="Assignment max points">
                      <input
                        id="course-assessment-points"
                        className={fieldClass}
                        type="number"
                        min={0}
                        value={formValues.max_points}
                        onChange={(event) => updateAssessmentForm({ max_points: event.target.value })}
                      />
                    </Field>
                  ) : (
                    <Field htmlFor="course-assessment-attempts" label="Max attempts">
                      <input
                        id="course-assessment-attempts"
                        className={fieldClass}
                        type="number"
                        min={1}
                        value={formValues.max_attempts}
                        onChange={(event) => updateAssessmentForm({ max_attempts: event.target.value })}
                      />
                    </Field>
                  )}
                  {saveAssessmentMutation.isError ? (
                    <ErrorState title="Assessment save failed" error={saveAssessmentMutation.error} />
                  ) : null}
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="submit"
                      loading={saveAssessmentMutation.isPending}
                      loadingLabel="Saving"
                      disabled={!formValues.title.trim() || !institutionId}
                    >
                      {formValues.id ? 'Update assessment' : 'Create assessment'}
                    </Button>
                    {formValues.id ? (
                      <Button variant="secondary" onClick={() => setFormValues(emptyAssessmentForm)}>
                        Cancel edit
                      </Button>
                    ) : null}
                  </div>
                </form>
              </Panel>
              <Panel title="Attach questions">
                <form
                  className="space-y-4"
                  onSubmit={(event) => {
                    event.preventDefault();
                    attachMutation.mutate();
                  }}
                >
                  <Field htmlFor="attach-assessment-title" label="Assessment" required>
                    <select
                      id="attach-assessment-title"
                      className={fieldClass}
                      required
                      value={attachAssessmentId}
                      onChange={(event) => setAttachAssessmentId(event.target.value)}
                    >
                      <option value="">Select assessment</option>
                      {assessments.map((assessment) => (
                        <option key={assessment.id} value={assessment.id}>
                          {itemTitle(assessment)}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field htmlFor="attach-bank-title" label="Question bank" required>
                    <select
                      id="attach-bank-title"
                      className={fieldClass}
                      required
                      value={attachBankId}
                      onChange={(event) => {
                        setAttachBankId(event.target.value);
                        setSelectedQuestionIds([]);
                      }}
                    >
                      <option value="">Select bank</option>
                      {banks.map((bank) => (
                        <option key={bank.id} value={bank.id}>
                          {itemTitle(bank)}
                        </option>
                      ))}
                    </select>
                  </Field>
                  {questionsQuery.isLoading ? <LoadingState label="Loading questions" /> : null}
                  {questions.length ? (
                    <div className="space-y-2">
                      {questions.map((question) => (
                        <label
                          className="flex gap-3 rounded-panel border border-slate-200 bg-white p-3 text-sm"
                          key={question.id}
                        >
                          <input
                            type="checkbox"
                            className="mt-1 h-4 w-4 rounded border-slate-300 text-emerald-700"
                            checked={selectedQuestionIds.includes(question.id)}
                            onChange={(event) => {
                              setSelectedQuestionIds((current) =>
                                event.target.checked
                                  ? [...current, question.id]
                                  : current.filter((questionId) => questionId !== question.id)
                              );
                            }}
                          />
                          <span>
                            <span className="font-medium text-slate-900">
                              {question.prompt || itemTitle(question)}
                            </span>
                            <span className="mt-1 block text-xs text-slate-500">
                              {question.question_type || 'question'} · {question.points ?? 0} points
                            </span>
                          </span>
                        </label>
                      ))}
                    </div>
                  ) : attachBankId && questionsQuery.data ? (
                    <EmptyState message="No questions are available in this bank." />
                  ) : null}
                  {attachMutation.isError ? <ErrorState title="Attach failed" error={attachMutation.error} /> : null}
                  <Button
                    type="submit"
                    loading={attachMutation.isPending}
                    loadingLabel="Attaching"
                    disabled={!attachAssessmentId || !selectedQuestionIds.length}
                  >
                    Replace attached questions
                  </Button>
                </form>
              </Panel>
            </div>
            <Panel title="Course assessments">
              {assessmentsQuery.isLoading ? <LoadingState label="Loading assessments" /> : null}
              {assessmentsQuery.isError ? <ErrorState error={assessmentsQuery.error} onRetry={() => void assessmentsQuery.refetch()} /> : null}
              {assessments.length ? (
                <ul className="divide-y divide-slate-100">
                  {assessments.map((assessment) => (
                    <li className="flex flex-wrap items-center justify-between gap-3 py-3" key={assessment.id}>
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-medium text-slate-950">{itemTitle(assessment)}</span>
                          <StatusBadge value={assessment.status ?? null} />
                        </div>
                        <div className="mt-1 text-xs text-slate-500">
                          {assessment.assessment_type || 'assessment'}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button variant="secondary" size="sm" onClick={() => setFormValues(toAssessmentForm(assessment))}>
                          Edit
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => lifecycleMutation.mutate({ assessmentId: assessment.id, action: 'publish' })}
                        >
                          Publish
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => lifecycleMutation.mutate({ assessmentId: assessment.id, action: 'close' })}
                        >
                          Close
                        </Button>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : assessmentsQuery.data ? (
                <EmptyState message="No assessments have been created for this course." />
              ) : null}
              {lifecycleMutation.isError ? (
                <div className="mt-4">
                  <ErrorState title="Lifecycle action failed" error={lifecycleMutation.error} />
                </div>
              ) : null}
            </Panel>
          </div>
        ) : null}
      </CourseWorkspaceShell>
    </PortalLayout>
  );
}
