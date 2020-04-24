from cffi import FFI

ffibuilder = FFI()

with open("./regexutil.h") as file:
    header = file.read()

ffibuilder.cdef(header)
ffibuilder.set_source(
    "_regexutil",
    header
    + r"""
#include <stdint.h>

SparseSet *sparseset_init(int maxValue, int capacity) {
  SparseSet *s = malloc(sizeof(SparseSet));
  s->capacity = capacity;
  s->size = 0, s->max_value = maxValue;
  s->dense = calloc(capacity, sizeof(int));
  s->sparse = calloc(maxValue + 1, sizeof(int));
  return s;
}

void sparseset_deinit(SparseSet *s) {
  free(s->dense);
  free(s->sparse);
  free(s);
}

int sparseset_contains(SparseSet *s, int value) {
  if (value > s->max_value) {
    return -1;
  }

  if (s->sparse[value] < s->size && s->dense[s->sparse[value]] == value) {
    return s->sparse[value];
  }

  return -1;
}

void sparseset_insert(SparseSet *s, int value) {
  if (value > s->max_value) {
    return;
  }

  if (s->size >= s->capacity) {
    return;
  }
  if (sparseset_contains(s, value) != -1) {
    return;
  }
  s->dense[s->size] = value;
  s->sparse[value] = s->size;

  s->size++;
}

void sparseset_remove(SparseSet *s, int value) {
  if (sparseset_contains(s, value) == -1) {
    return;
  }

  int temp = s->dense[s->size - 1];
  s->dense[s->sparse[value]] = temp;

  s->size -= 1;
}

void sparseset_clear(SparseSet *s) { s->size = 0; }

void sparseset_print(SparseSet *s) {
  for (int i = 0; i < s->size; i++) {
    printf("%d ", s->dense[i]);
  }
  printf("\n");
}

void sparseset_swap(SparseSet *s, SparseSet *otherS) {
  SparseSet temp = *s;
  *s = *otherS;
  *otherS = temp;
}

int is_word_byte(int byte) {
  if (!byte) {
    return 0;
  }
  return ((int)'A' <= byte && byte <= (int)'Z') ||
         ((int)'a' <= byte && byte <= (int)'z') ||
         ((int)'0' <= byte && byte <= (int)'9') || (byte == (int)'_');
}

int matches(int byte, int start, int end) {
  byte = byte > 0 ? byte : byte & 0xFF;
  return start <= byte && byte <= end;
}

Thread *thread_init(int numInsts, int nCaps) {
  Thread *t = malloc(sizeof(Thread));
  t->nslots = nCaps * 2;
  t->set = sparseset_init(numInsts, numInsts);
  t->caps = calloc(t->nslots*numInsts, sizeof(int));

  return t;
}

void thread_swap(Thread * t, Thread * otherT) {
  Thread temp = *t;
  *t = *otherT;
  *otherT = temp;
}

void thread_clear(Thread * t) {
  t->set->size = 0;
}

void thread_deinit(Thread *t) {
  free(t->caps);
  sparseset_deinit(t->set);
  free(t);
}

Matches * matches_init(int initial_cap) {
  Matches * m = malloc(sizeof(Matches));
  m->nmatch = 0;
  m->matches_slots_capacity = initial_cap;
  m->matches_slots = calloc(initial_cap, sizeof(int*));

  return m;
}

void matches_append(Matches * m, int * slots) {
  if (m->matches_slots_capacity == m->nmatch) {
    matches_resize(m, m->matches_slots_capacity*2);
  }
  int* match_slots = calloc(2, sizeof(int));
  match_slots[0] = slots[0];
  match_slots[1] = slots[1];
  m->matches_slots[m->nmatch++] = match_slots;
}

void matches_resize(Matches * m, int capacity) {
  int** new_matches = realloc(m->matches_slots, sizeof(int*) * capacity);
  if(new_matches) {
    m->matches_slots = new_matches;
    m->matches_slots_capacity = capacity;
  }
}

void matches_deinit(Matches * m) {
  for (int i = 0; i < m->nmatch; m++) {
    free(m->matches_slots[i]);
  }
  free(m->matches_slots);
}
""",
)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
