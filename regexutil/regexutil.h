typedef struct SparseSet {
  int *dense;
  int *sparse;
  int size;
  int capacity;
  int max_value;
} SparseSet;

SparseSet *sparseset_init(int maxValue, int capacity);
void sparseset_deinit(SparseSet *s);
int sparseset_contains(SparseSet *s, int);
void sparseset_insert(SparseSet *s, int element);
void sparseset_remove(SparseSet *s, int);
void sparseset_print(SparseSet *s);
void sparseset_clear(SparseSet *s);
void sparseset_swap(SparseSet *s, SparseSet *otherS);

typedef struct Thread {
  int *caps;
  int nslots;
  SparseSet *set;
} Thread;

Thread *thread_init(int numInsts, int nCaps);
void thread_deinit(Thread *t);
void thread_swap(Thread *t, Thread *otherT);
void thread_clear(Thread *t);

typedef struct Matches {
  int nmatch;
  int matches_slots_capacity;
  int **matches_slots;
} Matches;

Matches *matches_init(int initial_cap);
void matches_deinit(Matches *m);
void matches_resize(Matches *m, int capacity);
void matches_append(Matches *m, int *slots);

int is_word_byte(int byte);
int matches(int byte, int start, int end);
