import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { TagDto } from '../dtos/tag';

export const TagActions = createActionGroup({
  source: 'Tag',
  events: {
    'Fetch tags command': emptyProps(),
    'Fetch tags success event': props<{ tags: TagDto[] }>(),
    'Fetch tags failure event': props<{ error: string }>(),
  },
});
