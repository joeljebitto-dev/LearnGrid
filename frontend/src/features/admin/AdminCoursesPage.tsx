import {
  Archive,
  CheckCircle2,
  Pencil,
  Plus,
  RotateCcw,
  Search,
  Trash2,
  Users
} from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState, type FormEvent } from 'react';

import {
  createRoleAssignment,
  type SessionContext,
  type UserProfile
} from '../../api/auth';
import {
  archiveCourse,
  createCourse,
  deleteCourse,
  listCourses,
  publishCourse,
  updateCourse,
  type Course,
  type CourseDifficulty,
  type CoursePayload,
  type CourseStatus
} from '../../api/courses';
import {
  listInstitutions,
  listUserProfiles,
  type Institution
} from '../../api/users';
import { createEnrollment } from '../../api/enrollments';
import { toList } from '../../api/types';
import { adminInstitutionScope } from '../auth/session';
import { PortalLayout } from '../layout/PortalLayout';
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  LoadingState,
  PageHeader,
  PaginationControls,
  Panel,
  Select,
  StatusBadge,
  Textarea,
  Toolbar,
  Toast
} from '../shared/ui';

type CourseFormValues = {
  institution_id: string;
  owner_profile_id: string;
  title: string;
  slug: string;
  description: string;
  difficulty_level: CourseDifficulty | '';
};

type LifecycleAction = 'publish' | 'archive' | 'delete';

const courseStatuses: CourseStatus[] = ['draft', 'published', 'archived', 'deleted'];
const difficultyLevels: CourseDifficulty[] = ['beginner', 'intermediate', 'advanced'];

function emptyToNull(value?: string) {
  const normalized = value?.trim();
  return normalized ? normalized : null;
}

function courseTitle(course: Course) {
  return course.title || course.name || course.id;
}

function profileTitle(profile: UserProfile) {
  return (
    profile.display_name ||
    `${profile.first_name} ${profile.last_name}`.trim() ||
    profile.auth_account_id
  );
}

function institutionLabel(institution: Institution) {
  return `${institution.name} (${institution.code})`;
}

function institutionName(
  institutionId: string | null | undefined,
  institutionsById: Map<string, Institution>
) {
  if (!institutionId) {
    return 'Institution unavailable';
  }
  const institution = institutionsById.get(institutionId);
  return institution ? institutionLabel(institution) : institutionId;
}

function emptyCourseForm(context: SessionContext): CourseFormValues {
  return {
    institution_id:
      context.session.primary_role === 'institution_admin'
        ? adminInstitutionScope(context) ?? ''
        : '',
    owner_profile_id: '',
    title: '',
    slug: '',
    description: '',
    difficulty_level: ''
  };
}

function formFromCourse(course: Course): CourseFormValues {
  return {
    institution_id: String(course.institution_id ?? ''),
    owner_profile_id: String(course.owner_profile_id ?? ''),
    title: course.title ?? '',
    slug: course.slug ?? '',
    description: course.description ?? '',
    difficulty_level: course.difficulty_level ?? ''
  };
}

function createPayload(values: CourseFormValues, institutionId: string): CoursePayload {
  const payload: CoursePayload = {
    institution_id: institutionId,
    owner_profile_id: values.owner_profile_id,
    title: values.title.trim(),
    description: emptyToNull(values.description),
    difficulty_level: values.difficulty_level || null
  };
  const slug = values.slug.trim();
  if (slug) {
    payload.slug = slug;
  }
  return payload;
}

function updatePayload(values: CourseFormValues): Partial<CoursePayload> {
  const payload: Partial<CoursePayload> = {
    owner_profile_id: values.owner_profile_id,
    title: values.title.trim(),
    description: emptyToNull(values.description),
    difficulty_level: values.difficulty_level || null
  };
  const slug = values.slug.trim();
  if (slug) {
    payload.slug = slug;
  }
  return payload;
}

function hasNextPage(response: Awaited<ReturnType<typeof listCourses>> | undefined) {
  return Boolean(response && !Array.isArray(response) && response.next);
}

export function AdminCoursesPage({ context }: { context: SessionContext }) {
  const queryClient = useQueryClient();
  const isSuperAdmin = context.session.primary_role === 'super_admin';
  const institutionScope =
    context.session.primary_role === 'institution_admin' ? adminInstitutionScope(context) : null;
  const [page, setPage] = useState(1);
  const [searchDraft, setSearchDraft] = useState('');
  const [activeSearch, setActiveSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<CourseStatus | ''>('');
  const [difficultyFilter, setDifficultyFilter] = useState<CourseDifficulty | ''>('');
  const [institutionFilter, setInstitutionFilter] = useState('');
  const [institutionSearch, setInstitutionSearch] = useState('');
  const [ownerSearch, setOwnerSearch] = useState('');
  const [editingCourse, setEditingCourse] = useState<Course | null>(null);
  const [peopleCourse, setPeopleCourse] = useState<Course | null>(null);
  const [studentSearch, setStudentSearch] = useState('');
  const [peopleInstructorSearch, setPeopleInstructorSearch] = useState('');
  const [selectedStudentProfileId, setSelectedStudentProfileId] = useState('');
  const [selectedInstructorProfileId, setSelectedInstructorProfileId] = useState('');
  const [formValues, setFormValues] = useState<CourseFormValues>(() => emptyCourseForm(context));
  const activeInstitutionFilter = institutionScope ?? institutionFilter;

  const coursesQuery = useQuery({
    queryKey: [
      'admin-courses',
      activeInstitutionFilter || 'all',
      activeSearch,
      statusFilter,
      difficultyFilter,
      page
    ],
    queryFn: () =>
      listCourses({
        institution_id: activeInstitutionFilter || undefined,
        q: activeSearch || undefined,
        status: statusFilter || undefined,
        difficulty_level: difficultyFilter || undefined,
        sort: '-updated_at',
        page,
        page_size: 10
      })
  });

  const institutionsQuery = useQuery({
    queryKey: ['admin-course-institutions', institutionSearch],
    queryFn: () =>
      listInstitutions({
        q: institutionSearch.trim() || undefined,
        sort: 'name',
        page_size: 100
      }),
    enabled: isSuperAdmin
  });

  const selectedInstitutionId =
    editingCourse?.institution_id ?? institutionScope ?? formValues.institution_id;

  const instructorsQuery = useQuery({
    queryKey: ['admin-course-instructors', selectedInstitutionId || 'none', ownerSearch],
    queryFn: () =>
      listUserProfiles({
        institution_id: String(selectedInstitutionId),
        profile_type: 'instructor',
        status: 'active',
        q: ownerSearch.trim() || undefined,
        sort: 'last_name',
        page_size: 100
      }),
    enabled: Boolean(selectedInstitutionId)
  });
  const peopleInstitutionId = String(peopleCourse?.institution_id ?? '');
  const peopleStudentsQuery = useQuery({
    queryKey: ['admin-course-people-students', peopleInstitutionId || 'none', studentSearch],
    queryFn: () =>
      listUserProfiles({
        institution_id: peopleInstitutionId,
        profile_type: 'student',
        status: 'active',
        q: studentSearch.trim() || undefined,
        sort: 'last_name',
        page_size: 100
      }),
    enabled: Boolean(peopleCourse && peopleInstitutionId)
  });
  const peopleInstructorsQuery = useQuery({
    queryKey: [
      'admin-course-people-instructors',
      peopleInstitutionId || 'none',
      peopleInstructorSearch
    ],
    queryFn: () =>
      listUserProfiles({
        institution_id: peopleInstitutionId,
        profile_type: 'instructor',
        status: 'active',
        q: peopleInstructorSearch.trim() || undefined,
        sort: 'last_name',
        page_size: 100
      }),
    enabled: Boolean(peopleCourse && peopleInstitutionId)
  });

  const institutions = useMemo(
    () => institutionsQuery.data?.results ?? [],
    [institutionsQuery.data]
  );
  const instructors = instructorsQuery.data?.results ?? [];
  const peopleStudents = peopleStudentsQuery.data?.results ?? [];
  const peopleInstructors = peopleInstructorsQuery.data?.results ?? [];
  const institutionsById = useMemo(
    () =>
      new Map<string, Institution>(
        institutions.map((institution) => [institution.id, institution] as const)
      ),
    [institutions]
  );
  const courses = toList(coursesQuery.data);
  const isEditing = Boolean(editingCourse);
  const canSave = Boolean(
    String(selectedInstitutionId ?? '').trim() &&
      formValues.owner_profile_id.trim() &&
      formValues.title.trim()
  );

  const invalidateCourses = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['admin-courses'] }),
      queryClient.invalidateQueries({ queryKey: ['courses'] })
    ]);
  };

  const saveMutation = useMutation({
    mutationFn: (values: CourseFormValues) =>
      editingCourse
        ? updateCourse(editingCourse.id, updatePayload(values))
        : createCourse(createPayload(values, String(selectedInstitutionId))),
    onSuccess: async () => {
      setEditingCourse(null);
      setFormValues(emptyCourseForm(context));
      setOwnerSearch('');
      await invalidateCourses();
    }
  });

  const lifecycleMutation = useMutation({
    mutationFn: ({ action, courseId }: { action: LifecycleAction; courseId: string }) => {
      if (action === 'publish') {
        return publishCourse(courseId);
      }
      if (action === 'archive') {
        return archiveCourse(courseId);
      }
      return deleteCourse(courseId);
    },
    onSuccess: invalidateCourses
  });
  const addStudentMutation = useMutation({
    mutationFn: () => {
      if (!peopleCourse || !peopleInstitutionId || !selectedStudentProfileId) {
        throw new Error('Select a course and student before adding to the course.');
      }
      return createEnrollment({
        student_profile_id: selectedStudentProfileId,
        course_id: peopleCourse.id,
        institution_id: peopleInstitutionId,
        enrolled_by_profile_id: context.profile.id
      });
    },
    onSuccess: async () => {
      setSelectedStudentProfileId('');
      await queryClient.invalidateQueries({ queryKey: ['enrollments'] });
    }
  });
  const addInstructorMutation = useMutation({
    mutationFn: () => {
      if (!peopleCourse || !selectedInstructorProfileId) {
        throw new Error('Select a course and instructor before adding to the course.');
      }
      const instructor = peopleInstructors.find(
        (profile) => profile.id === selectedInstructorProfileId
      );
      if (!instructor?.auth_account_id) {
        throw new Error('Selected instructor does not have an auth account.');
      }
      return createRoleAssignment({
        account_id: instructor.auth_account_id,
        role_code: 'instructor',
        scope_type: 'course',
        scope_id: peopleCourse.id
      });
    },
    onSuccess: () => {
      setSelectedInstructorProfileId('');
    }
  });

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActiveSearch(searchDraft.trim());
    setPage(1);
  }

  function clearSearch() {
    setSearchDraft('');
    setActiveSearch('');
    setStatusFilter('');
    setDifficultyFilter('');
    setInstitutionFilter('');
    setPage(1);
  }

  function resetForm() {
    saveMutation.reset();
    setEditingCourse(null);
    setFormValues(emptyCourseForm(context));
    setOwnerSearch('');
    setInstitutionSearch('');
  }

  function startEdit(course: Course) {
    saveMutation.reset();
    setEditingCourse(course);
    setFormValues(formFromCourse(course));
    setOwnerSearch('');
    setInstitutionSearch('');
  }

  function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (canSave) {
      saveMutation.mutate(formValues);
    }
  }

  function setInstitution(institutionId: string) {
    setFormValues((current) => ({
      ...current,
      institution_id: institutionId,
      owner_profile_id: ''
    }));
    setOwnerSearch('');
  }

  function startPeople(course: Course) {
    setPeopleCourse(course);
    setStudentSearch('');
    setPeopleInstructorSearch('');
    setSelectedStudentProfileId('');
    setSelectedInstructorProfileId('');
    addStudentMutation.reset();
    addInstructorMutation.reset();
  }

  return (
    <PortalLayout context={context} activeNav="admin-courses">
      <PageHeader title="Courses" />

      <form onSubmit={submitSearch}>
        <Toolbar className="mb-5">
          <Field htmlFor="course-search" label="Search">
            <Input
              id="course-search"
              value={searchDraft}
              onChange={(event) => setSearchDraft(event.target.value)}
            />
          </Field>
          {isSuperAdmin ? (
            <Field htmlFor="course-institution-filter" label="Institution">
              <Select
                id="course-institution-filter"
                value={institutionFilter}
                onChange={(event) => {
                  setInstitutionFilter(event.target.value);
                  setPage(1);
                }}
              >
                <option value="">All institutions</option>
                {institutions.map((institution) => (
                  <option key={institution.id} value={institution.id}>
                    {institutionLabel(institution)}
                  </option>
                ))}
              </Select>
            </Field>
          ) : null}
          <Field htmlFor="course-status-filter" label="Status">
            <Select
              id="course-status-filter"
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value as CourseStatus | '');
                setPage(1);
              }}
            >
              <option value="">Any status</option>
              {courseStatuses.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </Select>
          </Field>
          <Field htmlFor="course-difficulty-filter" label="Difficulty">
            <Select
              id="course-difficulty-filter"
              value={difficultyFilter}
              onChange={(event) => {
                setDifficultyFilter(event.target.value as CourseDifficulty | '');
                setPage(1);
              }}
            >
              <option value="">Any difficulty</option>
              {difficultyLevels.map((difficulty) => (
                <option key={difficulty} value={difficulty}>
                  {difficulty}
                </option>
              ))}
            </Select>
          </Field>
          <div className="flex items-end gap-2">
            <Button type="submit" variant="secondary">
              <Search className="h-4 w-4" aria-hidden />
              Search
            </Button>
            <Button type="button" variant="ghost" onClick={clearSearch}>
              <RotateCcw className="h-4 w-4" aria-hidden />
              Reset
            </Button>
          </div>
        </Toolbar>
      </form>

      <div className="grid gap-5 xl:grid-cols-[400px_1fr]">
        <div className="space-y-5">
          <Panel title={isEditing ? 'Edit course' : 'Create course'}>
            <form className="space-y-4" onSubmit={submitForm}>
            {!isEditing && isSuperAdmin ? (
              <>
                <Field htmlFor="course-institution-search" label="Find institution">
                  <Input
                    id="course-institution-search"
                    value={institutionSearch}
                    onChange={(event) => setInstitutionSearch(event.target.value)}
                  />
                </Field>
                <Field htmlFor="course-institution" label="Institution" required>
                  <Select
                    id="course-institution"
                    value={formValues.institution_id}
                    onChange={(event) => setInstitution(event.target.value)}
                    required
                  >
                    <option value="">Select institution</option>
                    {institutions.map((institution) => (
                      <option key={institution.id} value={institution.id}>
                        {institutionLabel(institution)}
                      </option>
                    ))}
                  </Select>
                </Field>
                {institutionsQuery.isError ? (
                  <ErrorState title="Unable to load institutions" error={institutionsQuery.error} />
                ) : null}
              </>
            ) : null}

            {!isEditing && !isSuperAdmin ? (
              <div className="rounded-panel border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                <span className="font-medium text-slate-900">Institution</span>
                <div className="mt-1">Current institution</div>
              </div>
            ) : null}

            {isEditing ? (
              <div className="rounded-panel border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                <span className="font-medium text-slate-900">Institution</span>
                <div className="mt-1">
                  {!isSuperAdmin && editingCourse?.institution_id === institutionScope
                    ? 'Current institution'
                    : institutionName(editingCourse?.institution_id, institutionsById)}
                </div>
              </div>
            ) : null}

            <Field htmlFor="course-owner-search" label="Find instructor">
              <Input
                id="course-owner-search"
                value={ownerSearch}
                disabled={!selectedInstitutionId}
                onChange={(event) => setOwnerSearch(event.target.value)}
              />
            </Field>
            <Field htmlFor="course-owner" label="Owner instructor" required>
              <Select
                id="course-owner"
                value={formValues.owner_profile_id}
                disabled={!selectedInstitutionId}
                onChange={(event) =>
                  setFormValues((current) => ({
                    ...current,
                    owner_profile_id: event.target.value
                  }))
                }
                required
              >
                <option value="">Select instructor</option>
                {formValues.owner_profile_id && !instructors.some((profile) => profile.id === formValues.owner_profile_id) ? (
                  <option value={formValues.owner_profile_id}>{formValues.owner_profile_id}</option>
                ) : null}
                {instructors.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profileTitle(profile)}
                  </option>
                ))}
              </Select>
            </Field>
            {instructorsQuery.isError ? (
              <ErrorState title="Unable to load instructors" error={instructorsQuery.error} />
            ) : null}

            <Field htmlFor="course-title" label="Title" required>
              <Input
                id="course-title"
                value={formValues.title}
                onChange={(event) =>
                  setFormValues((current) => ({ ...current, title: event.target.value }))
                }
                required
              />
            </Field>
            <Field htmlFor="course-slug" label="Slug">
              <Input
                id="course-slug"
                value={formValues.slug}
                onChange={(event) =>
                  setFormValues((current) => ({ ...current, slug: event.target.value }))
                }
              />
            </Field>
            <Field htmlFor="course-difficulty" label="Difficulty">
              <Select
                id="course-difficulty"
                value={formValues.difficulty_level}
                onChange={(event) =>
                  setFormValues((current) => ({
                    ...current,
                    difficulty_level: event.target.value as CourseDifficulty | ''
                  }))
                }
              >
                <option value="">None</option>
                {difficultyLevels.map((difficulty) => (
                  <option key={difficulty} value={difficulty}>
                    {difficulty}
                  </option>
                ))}
              </Select>
            </Field>
            <Field htmlFor="course-description" label="Description">
              <Textarea
                id="course-description"
                rows={4}
                value={formValues.description}
                onChange={(event) =>
                  setFormValues((current) => ({ ...current, description: event.target.value }))
                }
              />
            </Field>

            {saveMutation.isError ? (
              <ErrorState
                title={isEditing ? 'Unable to update course' : 'Unable to create course'}
                error={saveMutation.error}
              />
            ) : null}
            {saveMutation.isSuccess ? (
              <Toast title={isEditing ? 'Course updated' : 'Course created'} tone="success" />
            ) : null}

            <div className="flex flex-wrap gap-2">
              <Button
                type="submit"
                disabled={!canSave}
                loading={saveMutation.isPending}
                loadingLabel={isEditing ? 'Updating' : 'Creating'}
              >
                <Plus className="h-4 w-4" aria-hidden />
                {isEditing ? 'Update course' : 'Create course'}
              </Button>
              {isEditing ? (
                <Button type="button" variant="secondary" onClick={resetForm}>
                  <RotateCcw className="h-4 w-4" aria-hidden />
                  Cancel edit
                </Button>
              ) : null}
            </div>
            </form>
          </Panel>

          <Panel
            title="Course people"
            description="Add active students and instructors to the selected course."
          >
            {!peopleCourse ? (
              <EmptyState message="Select Add people on a course to manage assignments." />
            ) : (
              <div className="space-y-5">
                <div className="rounded-panel border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                  <span className="font-medium text-slate-900">{courseTitle(peopleCourse)}</span>
                  <div className="mt-1">
                    Institution: {institutionName(peopleCourse.institution_id, institutionsById)}
                  </div>
                </div>

                <form
                  className="space-y-3"
                  onSubmit={(event) => {
                    event.preventDefault();
                    addStudentMutation.mutate();
                  }}
                >
                  <Field htmlFor="course-student-search" label="Find student">
                    <Input
                      id="course-student-search"
                      value={studentSearch}
                      onChange={(event) => setStudentSearch(event.target.value)}
                    />
                  </Field>
                  <Field htmlFor="course-student" label="Student">
                    <Select
                      id="course-student"
                      value={selectedStudentProfileId}
                      onChange={(event) => setSelectedStudentProfileId(event.target.value)}
                    >
                      <option value="">Select student</option>
                      {peopleStudents.map((profile) => (
                        <option key={profile.id} value={profile.id}>
                          {profileTitle(profile)}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  {peopleStudentsQuery.isLoading ? <LoadingState label="Loading students" /> : null}
                  {peopleStudentsQuery.isError ? (
                    <ErrorState
                      title="Unable to load students"
                      error={peopleStudentsQuery.error}
                    />
                  ) : null}
                  {addStudentMutation.isError ? (
                    <ErrorState title="Unable to add student" error={addStudentMutation.error} />
                  ) : null}
                  {addStudentMutation.isSuccess ? (
                    <Toast title="Student added to course" tone="success" />
                  ) : null}
                  <Button
                    type="submit"
                    disabled={!selectedStudentProfileId}
                    loading={addStudentMutation.isPending}
                    loadingLabel="Adding student"
                  >
                    <Plus className="h-4 w-4" aria-hidden />
                    Add student
                  </Button>
                </form>

                <form
                  className="space-y-3 border-t border-slate-200 pt-5"
                  onSubmit={(event) => {
                    event.preventDefault();
                    addInstructorMutation.mutate();
                  }}
                >
                  <Field htmlFor="course-people-instructor-search" label="Find instructor">
                    <Input
                      id="course-people-instructor-search"
                      value={peopleInstructorSearch}
                      onChange={(event) => setPeopleInstructorSearch(event.target.value)}
                    />
                  </Field>
                  <Field htmlFor="course-people-instructor" label="Instructor">
                    <Select
                      id="course-people-instructor"
                      value={selectedInstructorProfileId}
                      onChange={(event) => setSelectedInstructorProfileId(event.target.value)}
                    >
                      <option value="">Select instructor</option>
                      {peopleInstructors.map((profile) => (
                        <option key={profile.id} value={profile.id}>
                          {profileTitle(profile)}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  {peopleInstructorsQuery.isLoading ? (
                    <LoadingState label="Loading instructors" />
                  ) : null}
                  {peopleInstructorsQuery.isError ? (
                    <ErrorState
                      title="Unable to load instructors"
                      error={peopleInstructorsQuery.error}
                    />
                  ) : null}
                  {addInstructorMutation.isError ? (
                    <ErrorState
                      title="Unable to add instructor"
                      error={addInstructorMutation.error}
                    />
                  ) : null}
                  {addInstructorMutation.isSuccess ? (
                    <Toast title="Instructor added to course" tone="success" />
                  ) : null}
                  <Button
                    type="submit"
                    disabled={!selectedInstructorProfileId}
                    loading={addInstructorMutation.isPending}
                    loadingLabel="Adding instructor"
                  >
                    <Users className="h-4 w-4" aria-hidden />
                    Add instructor
                  </Button>
                </form>
              </div>
            )}
          </Panel>
        </div>

        <Panel
          title="Course directory"
          actions={
            <PaginationControls
              page={page}
              hasNext={hasNextPage(coursesQuery.data)}
              onPrevious={() => setPage((current) => Math.max(1, current - 1))}
              onNext={() => setPage((current) => current + 1)}
            />
          }
        >
          {coursesQuery.isLoading ? <LoadingState label="Loading courses" /> : null}
          {coursesQuery.isError ? (
            <ErrorState
              title="Unable to load courses"
              error={coursesQuery.error}
              onRetry={() => void coursesQuery.refetch()}
            />
          ) : null}
          {lifecycleMutation.isError ? (
            <div className="mb-4">
              <ErrorState title="Unable to update course lifecycle" error={lifecycleMutation.error} />
            </div>
          ) : null}
          {coursesQuery.data && !courses.length ? <EmptyState message="No courses found." /> : null}
          {courses.length ? (
            <div className="overflow-x-auto rounded-panel border border-slate-200 bg-white">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <caption className="sr-only">Courses</caption>
                <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3" scope="col">Title</th>
                    <th className="px-4 py-3" scope="col">Institution</th>
                    <th className="px-4 py-3" scope="col">Difficulty</th>
                    <th className="px-4 py-3" scope="col">Status</th>
                    <th className="px-4 py-3" scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {courses.map((course) => (
                    <tr key={course.id}>
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-950">{courseTitle(course)}</div>
                        <div className="mt-1 text-xs text-slate-500">{course.slug || 'No slug'}</div>
                      </td>
                      <td className="px-4 py-3 text-slate-700">
                        {!isSuperAdmin && course.institution_id === institutionScope
                          ? 'Current institution'
                          : institutionName(course.institution_id, institutionsById)}
                      </td>
                      <td className="px-4 py-3 text-slate-700">
                        {course.difficulty_level ? <Badge>{course.difficulty_level}</Badge> : 'None'}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge value={course.status} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            aria-label={`Edit ${courseTitle(course)}`}
                            onClick={() => startEdit(course)}
                          >
                            <Pencil className="h-4 w-4" aria-hidden />
                            Edit
                          </Button>
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            aria-label={`Add people to ${courseTitle(course)}`}
                            onClick={() => startPeople(course)}
                          >
                            <Users className="h-4 w-4" aria-hidden />
                            Add people
                          </Button>
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            aria-label={`Publish ${courseTitle(course)}`}
                            disabled={course.status === 'published' || course.status === 'deleted'}
                            loading={
                              lifecycleMutation.isPending &&
                              lifecycleMutation.variables?.action === 'publish' &&
                              lifecycleMutation.variables.courseId === course.id
                            }
                            loadingLabel="Publishing"
                            onClick={() =>
                              lifecycleMutation.mutate({ action: 'publish', courseId: course.id })
                            }
                          >
                            <CheckCircle2 className="h-4 w-4" aria-hidden />
                            Publish
                          </Button>
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            aria-label={`Archive ${courseTitle(course)}`}
                            disabled={course.status === 'archived' || course.status === 'deleted'}
                            loading={
                              lifecycleMutation.isPending &&
                              lifecycleMutation.variables?.action === 'archive' &&
                              lifecycleMutation.variables.courseId === course.id
                            }
                            loadingLabel="Archiving"
                            onClick={() =>
                              lifecycleMutation.mutate({ action: 'archive', courseId: course.id })
                            }
                          >
                            <Archive className="h-4 w-4" aria-hidden />
                            Archive
                          </Button>
                          <Button
                            type="button"
                            variant="destructive"
                            size="sm"
                            aria-label={`Delete ${courseTitle(course)}`}
                            disabled={course.status === 'deleted'}
                            loading={
                              lifecycleMutation.isPending &&
                              lifecycleMutation.variables?.action === 'delete' &&
                              lifecycleMutation.variables.courseId === course.id
                            }
                            loadingLabel="Deleting"
                            onClick={() =>
                              lifecycleMutation.mutate({ action: 'delete', courseId: course.id })
                            }
                          >
                            <Trash2 className="h-4 w-4" aria-hidden />
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </Panel>
      </div>
    </PortalLayout>
  );
}
