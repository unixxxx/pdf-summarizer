import { FormControl } from '@angular/forms';

type SnakeToCamelCaseKey<S extends string> = S extends `${infer T}_${infer U}`
  ? `${Lowercase<T>}${Capitalize<SnakeToCamelCaseKey<U>>}`
  : Lowercase<S>;

export type ToCamelCase<T> = {
  [K in keyof T as SnakeToCamelCaseKey<K & string>]: T[K] extends object
    ? T[K] extends Array<unknown>
      ? T[K]
      : ToCamelCase<T[K]>
    : T[K];
};

export type ToFormControls<T> = {
  [K in keyof T]: FormControl<T[K]>;
};
