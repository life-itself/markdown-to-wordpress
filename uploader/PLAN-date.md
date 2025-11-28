## Task 1: Support date extraction and fallback when uploading posts

Add date parsing in the markdown layer: prefer `date`, fall back to `created`, otherwise leave unset for WordPress to default to today.

Ensure WordPress upload layer sets current date only when upstream did not supply one.

Add tests in markdown layer to cover `date`, `created`, and missing date cases; add E2E test plan stub for the same scenarios.

## Acceptance Criteria:

- [x] Markdown parsing returns the `date` value when present.
- [x] Markdown parsing returns the `created` value when `date` is absent.
- [x] When neither field exists, markdown layer leaves date undefined; WordPress layer assigns today's date on upload.
- [x] Tests exist for markdown date extraction logic as unit test
- [ ] Tests exist in E2E tests covering that case (inspect for date that should show up for at least one of the uploaded posts)

Raw dictation

> OK, I want to outline adding dates to your posts. So I want to make sure I mark down there extracts the date, which should be either in the date field or in the created field. Either one of if the date field use that field, if there's a creative field use that field. So what I mean, sorry, use the date field primarily if fall back to the created field. And if not, I guess you set today's date. Actually, don't set today's date. Let's do that the WordPress layer. So at the WordPress layer, if you don't set the date, let's set it to today when we do the uploading. And I want to suit a test for that in the markdown layer. And I think we could also set a test for that in the end to end tests, even though we can't run them. So please distill that. We're going to then out of that create like a small description of this issue and then the acceptance criteria for it as
