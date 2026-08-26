import { test, expect } from '@playwright/test';
import { getPrimaryE2EUser, hasSupabasePublicConfig } from './helpers/credentials';
import {
  cardByName,
  confirmDestructive,
  loginViaUi,
  logoutViaUi,
  uniqueId,
} from './helpers/ui';

const hasAuth = Boolean(getPrimaryE2EUser()) && hasSupabasePublicConfig();

test.describe('Core Daily Driver lifecycles', () => {
  test.skip(
    !hasAuth,
    'CORE E2E BLOCKED: E2E_EMAIL/E2E_PASSWORD and/or NEXT_PUBLIC_SUPABASE_* are not set. Credentials and keys were not invented.'
  );

  test('FLOW 1 Venture: create, visible, reload, edit, logout/login persist, archive', async ({
    page,
  }) => {
    const user = getPrimaryE2EUser();
    if (!user) return;

    const name = uniqueId('QA-Venture');
    const renamed = `${name}-edited`;

    await page.goto('/ventures');
    await expect(page.getByRole('heading', { name: /venture management/i })).toBeVisible();

    await page.getByTestId('venture-create').click();
    await page.getByPlaceholder('Venture name *').fill(name);
    await page.getByPlaceholder('Description (optional)').fill('Independent QA lifecycle');
    await page.getByRole('button', { name: 'Create Venture' }).click();

    const created = cardByName(page, 'venture-card', name);
    await expect(created).toBeVisible();
    await expect(created.getByRole('heading', { name })).toHaveText(name);

    await page.reload();
    await expect(cardByName(page, 'venture-card', name)).toBeVisible();

    await cardByName(page, 'venture-card', name).getByRole('button', { name: 'Edit venture' }).click();
    const editPanel = page.getByTestId('venture-edit');
    await expect(editPanel).toBeVisible();
    const nameInput = editPanel.locator('input').first();
    await expect(nameInput).toHaveValue(name);
    await nameInput.fill(renamed);
    await editPanel.getByRole('button', { name: /save/i }).click();
    await expect(cardByName(page, 'venture-card', renamed)).toBeVisible();

    await logoutViaUi(page);
    await loginViaUi(page, user);
    await page.goto('/ventures');
    await expect(cardByName(page, 'venture-card', renamed)).toBeVisible();

    await cardByName(page, 'venture-card', renamed)
      .getByRole('button', { name: 'Archive venture' })
      .click();
    await confirmDestructive(page, 'Archive Venture');
    await expect(cardByName(page, 'venture-card', renamed)).toHaveCount(0);
  });

  test('FLOW 2 Project: linked to venture, reload, edit, persist, archive', async ({ page }) => {
    const user = getPrimaryE2EUser();
    if (!user) return;

    const ventureName = uniqueId('QA-V-for-Project');
    const projectName = uniqueId('QA-Project');
    const renamed = `${projectName}-edited`;

    await page.goto('/ventures');
    await page.getByTestId('venture-create').click();
    await page.getByPlaceholder('Venture name *').fill(ventureName);
    await page.getByRole('button', { name: 'Create Venture' }).click();
    await expect(cardByName(page, 'venture-card', ventureName)).toBeVisible();

    await page.goto('/projects');
    await expect(page.getByRole('heading', { name: /project portfolio/i })).toBeVisible();
    await page.getByTestId('project-create').click();
    await page.getByPlaceholder('Project name *').fill(projectName);
    await page.locator('select').filter({ hasText: 'No venture (optional)' }).selectOption({
      label: ventureName,
    });
    await page.getByPlaceholder('Description (optional)').fill('Linked project');
    await page.getByRole('button', { name: 'Create Project' }).click();

    const projectCard = cardByName(page, 'project-card', projectName);
    await expect(projectCard).toBeVisible();
    await expect(projectCard.getByText(ventureName)).toBeVisible();

    await page.reload();
    await expect(cardByName(page, 'project-card', projectName).getByText(ventureName)).toBeVisible();

    await cardByName(page, 'project-card', projectName)
      .getByRole('button', { name: 'Edit project' })
      .click();
    const editInput = cardByName(page, 'project-card', projectName).locator('input').first();
    await expect(editInput).toHaveValue(projectName);
    await editInput.fill(renamed);
    await cardByName(page, 'project-card', projectName).getByRole('button', { name: /save/i }).click();
    await expect(cardByName(page, 'project-card', renamed).getByText(ventureName)).toBeVisible();

    await logoutViaUi(page);
    await loginViaUi(page, user);
    await page.goto('/projects');
    await expect(cardByName(page, 'project-card', renamed).getByText(ventureName)).toBeVisible();

    await cardByName(page, 'project-card', renamed)
      .getByRole('button', { name: 'Archive project' })
      .click();
    await confirmDestructive(page, 'Archive Project');
    await expect(cardByName(page, 'project-card', renamed)).toHaveCount(0);

    await page.goto('/ventures');
    await cardByName(page, 'venture-card', ventureName)
      .getByRole('button', { name: 'Archive venture' })
      .click();
    await confirmDestructive(page, 'Archive Venture');
  });

  test('FLOW 3 Task: venture→project link, status cycle, persist, delete', async ({ page }) => {
    const user = getPrimaryE2EUser();
    if (!user) return;

    const ventureName = uniqueId('QA-V-for-Task');
    const projectName = uniqueId('QA-P-for-Task');
    const taskTitle = uniqueId('QA-Task');

    await page.goto('/ventures');
    await page.getByTestId('venture-create').click();
    await page.getByPlaceholder('Venture name *').fill(ventureName);
    await page.getByRole('button', { name: 'Create Venture' }).click();
    await expect(cardByName(page, 'venture-card', ventureName)).toBeVisible();

    await page.goto('/projects');
    await page.getByTestId('project-create').click();
    await page.getByPlaceholder('Project name *').fill(projectName);
    await page.locator('select').filter({ hasText: 'No venture (optional)' }).selectOption({
      label: ventureName,
    });
    await page.getByRole('button', { name: 'Create Project' }).click();
    await expect(cardByName(page, 'project-card', projectName)).toBeVisible();

    await page.goto('/tasks');
    await expect(page.getByRole('heading', { name: /task execution engine/i })).toBeVisible();
    await page.getByRole('button', { name: /add venture, project, priority, due date/i }).click();
    await page.locator('select').filter({ hasText: 'Venture (optional)' }).selectOption({
      label: ventureName,
    });
    await page.locator('select').filter({ hasText: 'Project (optional)' }).selectOption({
      label: projectName,
    });
    await page.getByTestId('task-quick-input').fill(taskTitle);
    await page.getByRole('button', { name: 'Add' }).click();

    const row = page.getByTestId('task-row').filter({ hasText: taskTitle });
    await expect(row).toBeVisible();
    await expect(row.getByText(ventureName)).toBeVisible();
    await expect(row.getByText(projectName)).toBeVisible();
    await expect(row.getByText(/^todo$/i)).toBeVisible();

    await row.getByTestId('task-status').click();
    await expect(row.getByText(/in progress/i)).toBeVisible();
    await row.getByTestId('task-status').click();
    await expect(row.getByText(/^done$/i)).toBeVisible();

    await page.reload();
    const reloaded = page.getByTestId('task-row').filter({ hasText: taskTitle });
    await expect(reloaded.getByText(/^done$/i)).toBeVisible();
    await expect(reloaded.getByText(ventureName)).toBeVisible();
    await expect(reloaded.getByText(projectName)).toBeVisible();

    await logoutViaUi(page);
    await loginViaUi(page, user);
    await page.goto('/tasks');
    await expect(page.getByTestId('task-row').filter({ hasText: taskTitle })).toBeVisible();

    await page
      .getByTestId('task-row')
      .filter({ hasText: taskTitle })
      .getByRole('button', { name: 'Delete task' })
      .click();
    await confirmDestructive(page, 'Delete Task');
    await expect(page.getByTestId('task-row').filter({ hasText: taskTitle })).toHaveCount(0);

    await page.goto('/projects');
    await cardByName(page, 'project-card', projectName)
      .getByRole('button', { name: 'Archive project' })
      .click();
    await confirmDestructive(page, 'Archive Project');
    await page.goto('/ventures');
    await cardByName(page, 'venture-card', ventureName)
      .getByRole('button', { name: 'Archive venture' })
      .click();
    await confirmDestructive(page, 'Archive Venture');
  });

  test('FLOW 4 Person: create, search, detail, edit, persist, archive', async ({ page }) => {
    const user = getPrimaryE2EUser();
    if (!user) return;

    const personName = uniqueId('QA Person');
    const renamed = `${personName} Edited`;

    await page.goto('/people');
    await expect(page.getByRole('heading', { name: /relationship crm/i })).toBeVisible();
    await page.getByTestId('person-create').click();
    await expect(page).toHaveURL(/\/people\/new/);

    await page.locator('input[required]').first().fill(personName);
    await page.getByRole('button', { name: 'Create Contact' }).click();
    await expect(page).toHaveURL(/\/people$/);
    await expect(cardByName(page, 'person-card', personName)).toBeVisible();

    await page.getByTestId('people-search').fill(personName);
    await expect(cardByName(page, 'person-card', personName)).toBeVisible();
    await expect(page.getByTestId('person-card')).toHaveCount(1);

    await cardByName(page, 'person-card', personName).getByRole('link', { name: /view/i }).click();
    await expect(page).toHaveURL(/\/people\/[0-9a-f-]{36}$/i);
    await expect(page.getByRole('heading', { name: personName })).toBeVisible();

    await page.getByTestId('person-edit').click();
    await expect(page).toHaveURL(/\/edit$/);
    await expect(page.getByTestId('person-edit')).toBeVisible();
    const nameField = page.getByTestId('person-edit').locator('input').first();
    await expect(nameField).toHaveValue(personName);
    await nameField.fill(renamed);
    await page.getByRole('button', { name: 'Save Changes' }).click();
    await expect(page.getByRole('heading', { name: renamed })).toBeVisible();

    await page.reload();
    await expect(page.getByRole('heading', { name: renamed })).toBeVisible();

    await logoutViaUi(page);
    await loginViaUi(page, user);
    await page.goto('/people');
    await page.getByTestId('people-search').fill(renamed);
    await expect(cardByName(page, 'person-card', renamed)).toBeVisible();

    await cardByName(page, 'person-card', renamed).getByRole('link', { name: /view/i }).click();
    await page.getByRole('button', { name: /archive contact/i }).click();
    await confirmDestructive(page, 'Archive Contact');
    await expect(page).toHaveURL(/\/people$/);
    await page.getByTestId('people-search').fill(renamed);
    await expect(page.getByText(/no matches/i)).toBeVisible();
  });
});
