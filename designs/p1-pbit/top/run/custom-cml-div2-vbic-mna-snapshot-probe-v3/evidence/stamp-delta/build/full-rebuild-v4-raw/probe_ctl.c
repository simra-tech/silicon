#include "ngspice/cktdefs.h"
#include <stddef.h>
#include <stdio.h>
struct layout { size_t size, mode, diag, bypass, time_, rhs; };
const struct layout LAYOUT = { sizeof(CKTcircuit), offsetof(CKTcircuit, CKTmode),
  (size_t)-1,
  offsetof(CKTcircuit, CKTbypass), offsetof(CKTcircuit, CKTtime),
  offsetof(CKTcircuit, CKTrhs) };
int main(void){ return (int)LAYOUT.size; }
