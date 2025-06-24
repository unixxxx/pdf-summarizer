import { AsyncDataItem } from '../../core/utils/async-data-item';
import { User } from '../../core/interfaces/user.interface';

export interface AuthState {
  user: AsyncDataItem<User | undefined>;
}
