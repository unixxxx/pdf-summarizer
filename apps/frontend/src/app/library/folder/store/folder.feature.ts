import { createFeature, createSelector } from '@ngrx/store';
import { folderReducer } from './folder.reducer';
import {
  AsyncDataItemState,
  unwrapAsyncDataItem,
} from '../../../core/utils/async-data-item';
import { flattenFolders } from '../utils/folder';

export const folderFeature = createFeature({
  name: 'folder',
  reducer: folderReducer,
  extraSelectors: ({ selectFolder }) => ({
    selectFlattenFolders: createSelector(selectFolder, (asyncFolder) => {
      if (asyncFolder.state !== AsyncDataItemState.LOADED) {
        return [];
      }
      return flattenFolders(unwrapAsyncDataItem(asyncFolder).folders);
    }),
  }),
});
