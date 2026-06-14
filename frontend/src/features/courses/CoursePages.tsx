import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import type { SessionContext } from '../../api/auth';
import {
  archiveCourse,
  createCourse,
  createLesson,
  createModule,
  createTopic,
  deleteCourse,
  getCourse,
  getCourseStructure,
  listCourses,
  publishCourse,
  publishLesson,
  type Course,
  type CoursePayload
} from '../../api/courses';
import { createEnrollment } from '../../api/enrollments';
import { createSignedAccess } from '../../api/content';
import { updateLessonProgress, updateVideoProgress } from '../../api/progress';
import { toList, type Entity } from '../../api/types';
import { PortalLayout } from '../layout/PortalLayout';
import {
  buttonClass,
  EmptyState,
  EntityList,
  ErrorState,
  fieldClass,
  Field,
  itemTitle,
  JsonPreview,
  LoadingState,
  PageHeader,
  Panel,
  parseCsv,
  secondaryButtonClass,
  StatusBadge
} from '../shared/ui';

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
      />
      <section className="mb-5 rounded border border-slate-200 bg-white p-4">
        <div className="grid gap-3 md:grid-cols-4">
          <Field htmlFor="catalog-q" label="Search">
            <input
              id="catalog-q"
              className={fieldClass}
              value={filters.q}
              onChange={(event) => {
                filters.setPage(1);
                filters.setQ(event.target.value);
              }}
            />
          </Field>
          <Field htmlFor="catalog-status" label="Status">
            <select
              id="catalog-status"
              className={fieldClass}
              value={filters.status}
              onChange={(event) => {
                filters.setPage(1);
                filters.setStatus(event.target.value);
              }}
            >
              <option value="published">Published</option>
              <option value="">Any permitted status</option>
              <option value="draft">Draft</option>
              <option value="archived">Archived</option>
            </select>
          </Field>
          <Field htmlFor="catalog-difficulty" label="Difficulty">
            <select
              id="catalog-difficulty"
              className={fieldClass}
              value={filters.difficulty}
              onChange={(event) => {
                filters.setPage(1);
                filters.setDifficulty(event.target.value);
              }}
            >
              <option value="">Any</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </Field>
          <div className="flex items-end gap-2">
            <button
              className={secondaryButtonClass}
              type="button"
              disabled={filters.page <= 1}
              onClick={() => filters.setPage(Math.max(1, filters.page - 1))}
            >
              Previous
            </button>
            <button
              className={secondaryButtonClass}
              type="button"
              onClick={() => filters.setPage(filters.page + 1)}
            >
              Next
            </button>
          </div>
        </div>
      </section>

      {query.isLoading ? <LoadingState label="Loading courses" /> : null}
      {query.isError ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : null}
      {query.data ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {courses.length ? (
            courses.map((course) => (
              <article className="rounded border border-slate-200 bg-white p-5" key={course.id}>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-lg font-semibold text-slate-950">{itemTitle(course)}</h3>
                  <StatusBadge value={course.status} />
                </div>
                <p className="mt-2 line-clamp-3 text-sm text-slate-600">
                  {String(course.description || 'No course description provided.')}
                </p>
                <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                  <span>{course.difficulty_level || 'unspecified'} difficulty</span>
                  <span>{course.categories?.length ?? 0} categories</span>
                  <span>{course.tags?.length ?? 0} tags</span>
                </div>
                <Link
                  className="mt-4 inline-flex text-sm font-semibold text-emerald-700"
                  to={`/dashboard/student/courses/${course.id}`}
                >
                  View course
                </Link>
              </article>
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
          <PageHeader title={itemTitle(query.data)} description={String(query.data.description || '')}>
            <div className="flex flex-wrap gap-2">
              <button
                className={buttonClass}
                type="button"
                disabled={enrollMutation.isPending}
                onClick={() => enrollMutation.mutate(query.data)}
              >
                {enrollMutation.isPending ? 'Enrolling' : 'Enroll'}
              </button>
              <Link className={secondaryButtonClass} to={`/dashboard/student/courses/${query.data.id}/learn`}>
                Start learning
              </Link>
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
                {structureQuery.data.modules?.length ? (
                  <div className="space-y-4">
                    {structureQuery.data.modules.map((module) => (
                      <section className="rounded border border-slate-200 p-4" key={module.id}>
                        <h4 className="font-semibold text-slate-900">{itemTitle(module)}</h4>
                        <ul className="mt-3 space-y-2 text-sm text-slate-700">
                          {module.lessons?.map((lesson) => (
                            <li key={lesson.id}>
                              {itemTitle(lesson)}
                              {lesson.topics?.length ? ` · ${lesson.topics.length} topics` : ''}
                            </li>
                          ))}
                        </ul>
                      </section>
                    ))}
                  </div>
                ) : (
                  <EmptyState message="No modules are available yet." />
                )}
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
      <PageHeader title="Learning Player" description="Read lesson content and update progress." />
      {query.isLoading ? <LoadingState label="Loading lesson" /> : null}
      {query.isError ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : null}
      {query.data ? (
        <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
          <Panel title={firstLesson ? itemTitle(firstLesson) : 'No lesson selected'}>
            {firstLesson ? (
              <div className="space-y-4 text-sm text-slate-700">
                <p>{String(firstLesson.summary || 'This lesson has no summary yet.')}</p>
                {firstTopic ? (
                  <div className="rounded border border-slate-200 p-4">
                    <h4 className="font-semibold text-slate-950">{itemTitle(firstTopic)}</h4>
                    <p className="mt-2 text-slate-600">
                      Content asset: {assetId || 'No content asset attached'}
                    </p>
                  </div>
                ) : null}
                <div className="flex flex-wrap gap-2">
                  <button className={buttonClass} type="button" onClick={() => lessonMutation.mutate()}>
                    Mark lesson complete
                  </button>
                  <button
                    className={secondaryButtonClass}
                    type="button"
                    disabled={!assetId}
                    onClick={() => videoMutation.mutate()}
                  >
                    Mark video complete
                  </button>
                  <button
                    className={secondaryButtonClass}
                    type="button"
                    disabled={!assetId}
                    onClick={() => accessMutation.mutate()}
                  >
                    Request access link
                  </button>
                </div>
                {lessonMutation.isError ? <ErrorState title="Lesson progress failed" error={lessonMutation.error} /> : null}
                {videoMutation.isError ? <ErrorState title="Video progress failed" error={videoMutation.error} /> : null}
                {accessMutation.isError ? <ErrorState title="Access denied" error={accessMutation.error} /> : null}
                {accessMutation.data ? <JsonPreview value={accessMutation.data} /> : null}
              </div>
            ) : (
              <EmptyState message="This course has no playable lessons yet." />
            )}
          </Panel>
          <EntityList
            title="Course outline"
            response={(query.data.modules ?? []) as Entity[]}
            emptyMessage="No modules."
          />
        </div>
      ) : null}
    </PortalLayout>
  );
}

function coursePayloadFromForm(form: HTMLFormElement, context: SessionContext): CoursePayload {
  const data = new FormData(form);
  return {
    institution_id: String(data.get('institution_id') || context.profile.institution_id || ''),
    owner_profile_id: String(data.get('owner_profile_id') || context.profile.id),
    title: String(data.get('title') || ''),
    slug: String(data.get('slug') || '') || null,
    description: String(data.get('description') || '') || null,
    difficulty_level: String(data.get('difficulty_level') || '') || null,
    category_ids: parseCsv(String(data.get('category_ids') || '')),
    tag_ids: parseCsv(String(data.get('tag_ids') || '')),
    prerequisite_course_ids: parseCsv(String(data.get('prerequisite_course_ids') || '')),
    learning_outcomes: parseCsv(String(data.get('learning_outcomes') || '')).map((description, index) => ({
      description,
      position: index + 1
    }))
  };
}

export function InstructorCourseManagementPage({ context }: { context: SessionContext }) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['courses', 'instructor', context.profile.id],
    queryFn: () =>
      listCourses({
        owner_profile_id: context.profile.id,
        status: '',
        page_size: 20,
        sort: '-updated_at'
      })
  });
  const createMutation = useMutation({
    mutationFn: (payload: CoursePayload) => createCourse(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['courses'] });
    }
  });
  const lifecycleMutation = useMutation({
    mutationFn: ({ action, courseId }: { action: 'publish' | 'archive' | 'delete'; courseId: string }) => {
      if (action === 'publish') {
        return publishCourse(courseId);
      }
      if (action === 'archive') {
        return archiveCourse(courseId);
      }
      return deleteCourse(courseId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['courses'] });
    }
  });

  return (
    <PortalLayout context={context} activeNav="instructor-courses">
      <PageHeader title="Course Management" description="Create drafts and manage publish, archive, and delete workflows." />
      <div className="grid gap-5 xl:grid-cols-[420px_1fr]">
        <Panel title="Create draft course">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              createMutation.mutate(coursePayloadFromForm(event.currentTarget, context));
            }}
          >
            <Field htmlFor="course-title" label="Title">
              <input id="course-title" name="title" className={fieldClass} required />
            </Field>
            <Field htmlFor="course-institution" label="Institution ID">
              <input
                id="course-institution"
                name="institution_id"
                className={fieldClass}
                defaultValue={context.profile.institution_id ?? ''}
                required
              />
            </Field>
            <input name="owner_profile_id" type="hidden" value={context.profile.id} />
            <Field htmlFor="course-slug" label="Slug">
              <input id="course-slug" name="slug" className={fieldClass} />
            </Field>
            <Field htmlFor="course-difficulty" label="Difficulty">
              <select id="course-difficulty" name="difficulty_level" className={fieldClass}>
                <option value="">None</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </Field>
            <Field htmlFor="course-description" label="Description">
              <textarea id="course-description" name="description" className={fieldClass} rows={3} />
            </Field>
            <Field htmlFor="course-categories" label="Category IDs">
              <input id="course-categories" name="category_ids" className={fieldClass} placeholder="Comma-separated UUIDs" />
            </Field>
            <Field htmlFor="course-tags" label="Tag IDs">
              <input id="course-tags" name="tag_ids" className={fieldClass} placeholder="Comma-separated UUIDs" />
            </Field>
            <Field htmlFor="course-prerequisites" label="Prerequisite course IDs">
              <input id="course-prerequisites" name="prerequisite_course_ids" className={fieldClass} placeholder="Comma-separated UUIDs" />
            </Field>
            <Field htmlFor="course-outcomes" label="Learning outcomes">
              <textarea id="course-outcomes" name="learning_outcomes" className={fieldClass} rows={3} placeholder="Comma-separated outcomes" />
            </Field>
            {createMutation.isError ? <ErrorState title="Course creation failed" error={createMutation.error} /> : null}
            <button className={buttonClass} type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating' : 'Create draft'}
            </button>
          </form>
        </Panel>

        <div>
          {query.isLoading ? <LoadingState label="Loading courses" /> : null}
          {query.isError ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : null}
          {query.data ? (
            <EntityList
              title="Your courses"
              response={query.data}
              emptyMessage="No instructor courses yet."
              actions={(course) => (
                <>
                  <Link className={secondaryButtonClass} to={`/dashboard/instructor/courses/${course.id}/builder`}>
                    Builder
                  </Link>
                  <button className={secondaryButtonClass} type="button" onClick={() => lifecycleMutation.mutate({ action: 'publish', courseId: course.id })}>
                    Publish
                  </button>
                  <button className={secondaryButtonClass} type="button" onClick={() => lifecycleMutation.mutate({ action: 'archive', courseId: course.id })}>
                    Archive
                  </button>
                  <button className={secondaryButtonClass} type="button" onClick={() => lifecycleMutation.mutate({ action: 'delete', courseId: course.id })}>
                    Delete
                  </button>
                </>
              )}
            />
          ) : null}
        </div>
      </div>
    </PortalLayout>
  );
}

export function CourseBuilderPage({ context }: { context: SessionContext }) {
  const { courseId = '' } = useParams();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const query = useQuery({
    queryKey: ['courses', courseId, 'structure'],
    queryFn: () => getCourseStructure(courseId),
    enabled: Boolean(courseId)
  });
  const mutation = useMutation({
    mutationFn: async (form: HTMLFormElement) => {
      const data = new FormData(form);
      const action = String(data.get('action'));
      if (action === 'module') {
        return createModule(courseId, {
          title: String(data.get('title') || ''),
          description: String(data.get('description') || '') || null,
          position: Number(data.get('position') || 1)
        });
      }
      if (action === 'lesson') {
        return createLesson(String(data.get('module_id') || ''), {
          title: String(data.get('title') || ''),
          summary: String(data.get('description') || '') || null,
          position: Number(data.get('position') || 1),
          content_asset_id: String(data.get('content_asset_id') || '') || null
        });
      }
      return createTopic(String(data.get('lesson_id') || ''), {
        title: String(data.get('title') || ''),
        position: Number(data.get('position') || 1),
        content_asset_id: String(data.get('content_asset_id') || '') || null
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['courses', courseId, 'structure'] });
    }
  });
  const publishLessonMutation = useMutation({
    mutationFn: publishLesson,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['courses', courseId, 'structure'] });
    }
  });

  return (
    <PortalLayout context={context} activeNav="instructor-courses">
      <PageHeader title="Course Builder" description="Author modules, lessons, topics, ordering, and content attachments.">
        <button className={secondaryButtonClass} type="button" onClick={() => navigate('/dashboard/instructor/courses')}>
          Back to courses
        </button>
      </PageHeader>
      <div className="grid gap-5 xl:grid-cols-[420px_1fr]">
        <Panel title="Add structure item">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate(event.currentTarget);
            }}
          >
            <Field htmlFor="builder-action" label="Item type">
              <select id="builder-action" name="action" className={fieldClass}>
                <option value="module">Module</option>
                <option value="lesson">Lesson</option>
                <option value="topic">Topic</option>
              </select>
            </Field>
            <Field htmlFor="builder-title" label="Title">
              <input id="builder-title" name="title" className={fieldClass} required />
            </Field>
            <Field htmlFor="builder-position" label="Position">
              <input id="builder-position" name="position" className={fieldClass} type="number" min={1} defaultValue={1} />
            </Field>
            <Field htmlFor="builder-module" label="Module ID">
              <input id="builder-module" name="module_id" className={fieldClass} placeholder="Required for lessons" />
            </Field>
            <Field htmlFor="builder-lesson" label="Lesson ID">
              <input id="builder-lesson" name="lesson_id" className={fieldClass} placeholder="Required for topics" />
            </Field>
            <Field htmlFor="builder-asset" label="Content asset ID">
              <input id="builder-asset" name="content_asset_id" className={fieldClass} placeholder="Optional for lessons/topics" />
            </Field>
            <Field htmlFor="builder-description" label="Description or summary">
              <textarea id="builder-description" name="description" className={fieldClass} rows={3} />
            </Field>
            {mutation.isError ? <ErrorState title="Save failed" error={mutation.error} /> : null}
            <button className={buttonClass} type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Saving' : 'Save item'}
            </button>
          </form>
        </Panel>
        <div>
          {query.isLoading ? <LoadingState label="Loading structure" /> : null}
          {query.isError ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : null}
          {query.data ? (
            <Panel title={itemTitle(query.data)}>
              {query.data.modules?.length ? (
                <div className="space-y-4">
                  {query.data.modules.map((module) => (
                    <section className="rounded border border-slate-200 p-4" key={module.id}>
                      <h4 className="font-semibold text-slate-950">{itemTitle(module)}</h4>
                      <p className="mt-1 text-xs text-slate-500">Module ID: {module.id}</p>
                      <ul className="mt-3 space-y-2">
                        {module.lessons?.map((lesson) => (
                          <li className="rounded bg-slate-50 p-3 text-sm" key={lesson.id}>
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <span className="font-medium text-slate-900">{itemTitle(lesson)}</span>
                              <button
                                className={secondaryButtonClass}
                                type="button"
                                onClick={() => publishLessonMutation.mutate(lesson.id)}
                              >
                                Publish lesson
                              </button>
                            </div>
                            <p className="mt-1 text-xs text-slate-500">Lesson ID: {lesson.id}</p>
                            {lesson.topics?.length ? (
                              <ul className="mt-2 list-disc pl-5 text-xs text-slate-600">
                                {lesson.topics.map((topic) => (
                                  <li key={topic.id}>{itemTitle(topic)} · {topic.content_asset_id || 'no asset'}</li>
                                ))}
                              </ul>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    </section>
                  ))}
                </div>
              ) : (
                <EmptyState message="No modules yet. Create the first module to start authoring." />
              )}
            </Panel>
          ) : null}
        </div>
      </div>
    </PortalLayout>
  );
}
