import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { TagService } from '../services/tag.service';
import { switchMap } from 'rxjs/operators';
import { TagActions } from './tag.actions';
import { mapResponse } from '@ngrx/operators';

export class TagEffects {
  actions$ = inject(Actions);
  tagService = inject(TagService);

  fetchTags$ = createEffect(() =>
    this.actions$.pipe(
      ofType(TagActions.fetchTagsCommand),
      switchMap(() =>
        this.tagService.getTags().pipe(
          mapResponse({
            next: (tags) => TagActions.fetchTagsSuccessEvent({ tags }),
            error: (error: Error) =>
              TagActions.fetchTagsFailureEvent({ error: error.message }),
          })
        )
      )
    )
  );
}
