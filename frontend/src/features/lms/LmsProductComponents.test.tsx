import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test } from 'vitest';

import {
  AssignmentSubmissionState,
  AttemptStatusPanel,
  CertificateCard,
  CourseCard,
  CourseStructureTree,
  NotificationFeed,
  ProgressIndicator
} from './LmsProductComponents';

const course = {
  id: 'course-1',
  title: 'Biology Basics',
  description: 'Cells and systems',
  status: 'published',
  difficulty_level: 'beginner',
  categories: [{ id: 'category-1', name: 'Science' }],
  tags: [{ id: 'tag-1', name: 'STEM' }],
  prerequisite_course_ids: ['course-0'],
  learning_outcomes: [{ id: 'outcome-1', description: 'Explain cells.' }]
};

const structure = {
  ...course,
  modules: [
    {
      id: 'module-1',
      title: 'Cells',
      lessons: [
        {
          id: 'lesson-1',
          title: 'Cell structure',
          status: 'draft',
          content_asset_id: 'asset-1',
          topics: [{ id: 'topic-1', title: 'Nucleus', content_asset_id: null }]
        }
      ]
    }
  ]
};

test('course card renders metadata and call to action', () => {
  render(
    <MemoryRouter>
      <CourseCard course={course} href="/dashboard/student/courses/course-1" />
    </MemoryRouter>
  );

  expect(screen.getByRole('heading', { name: /biology basics/i })).toBeInTheDocument();
  expect(screen.getByText(/science/i)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /view course/i })).toHaveAttribute(
    'href',
    '/dashboard/student/courses/course-1'
  );
});

test('course structure tree renders modules, lessons, topics, and authoring affordance', () => {
  render(<CourseStructureTree structure={structure} mode="author" />);

  expect(screen.getByText(/module 1/i)).toBeInTheDocument();
  expect(screen.getByText(/cell structure/i)).toBeInTheDocument();
  expect(screen.getByText(/nucleus/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /publish lesson/i })).toBeInTheDocument();
  expect(screen.getByText(/drag order planned/i)).toBeInTheDocument();
});

test('attempt and assignment components expose timer, autosave, draft, and late states', () => {
  render(
    <>
      <AttemptStatusPanel status="in_progress" timeRemaining="05:00" autosaveState="Saved just now" />
      <AssignmentSubmissionState submissionId="submission-1" deadline="2026-06-30" late />
    </>
  );

  expect(screen.getByText(/05:00/i)).toBeInTheDocument();
  expect(screen.getByText(/saved just now/i)).toBeInTheDocument();
  expect(screen.getByText(/draft id submission-1/i)).toBeInTheDocument();
  expect(screen.getByText(/late/i)).toBeInTheDocument();
});

test('certificate and notification components expose product status', () => {
  render(
    <>
      <CertificateCard
        certificate={{
          id: 'certificate-1',
          certificate_number: 'LG-20260615-ABCDEF1234',
          valid: false,
          revoked_at: '2026-06-15T00:00:00Z'
        }}
      />
      <NotificationFeed
        notifications={[
          { id: 'notification-1', title: 'Grade published', event_type: 'GradePublished', read_at: null }
        ]}
      />
    </>
  );

  expect(screen.getByText(/LG-20260615-ABCDEF1234/i)).toBeInTheDocument();
  expect(screen.getByText(/revoked/i)).toBeInTheDocument();
  expect(screen.getByText(/grade published/i)).toBeInTheDocument();
  expect(screen.getByText(/unread/i)).toBeInTheDocument();
});

test('progress indicator renders a percentage value', () => {
  render(<ProgressIndicator value={72} />);

  expect(screen.getByText('72%')).toBeInTheDocument();
});
