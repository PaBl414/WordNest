import {test,expect} from '@playwright/test';

test('dashboard, language choice and local catalog',async({page})=>{
 await page.goto('/');
 await expect(page.getByRole('heading',{level:1})).toContainText('Twój kolejny krok');
 await page.getByLabel('Język nauki').selectOption('de');
 await page.getByRole('button',{name:'Słowa',exact:true}).click();
 await page.getByLabel('Szukaj słowa').fill('Mutter');
 await expect(page.locator('.word-row')).toHaveCount(1);
 await expect(page.locator('.word-row')).toContainText('matka');
});

test('custom vocabulary persists after reload',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Słowa',exact:true}).click();
 await page.getByRole('button',{name:'Dodaj słowo',exact:true}).click();
 const term='testword-'+Date.now();
 const modal=page.getByRole('dialog');
 await modal.getByLabel('Słowo / wyrażenie').fill(term);
 await modal.getByLabel('Polskie znaczenie',{exact:true}).fill('słowo testowe');
 await modal.getByRole('button',{name:'Zapisz słowo'}).click();
 await expect(modal).not.toBeVisible();
 await page.reload();
 await page.getByRole('button',{name:'Słowa',exact:true}).click();
 await page.getByLabel('Szukaj słowa').fill(term);
 await expect(page.locator('.word-row')).toContainText('słowo testowe');
});

test('flashcard can be revealed and resumed',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Nauka',exact:true}).click();
 await page.getByRole('button',{name:/Fiszki/}).click();
 await expect(page.getByRole('button',{name:'Odsłoń odpowiedź'})).toBeVisible();
 const prompt=await page.locator('.exercise h2').innerText();
 await page.reload();
 await expect(page.locator('.exercise h2')).toHaveText(prompt);
 await page.getByRole('button',{name:'Odsłoń odpowiedź'}).click();
 await page.getByRole('button',{name:'Umiem',exact:true}).click();
 await expect(page.getByRole('button',{name:'Dalej',exact:true})).toBeVisible();
});
