/* OS SIOV traffic under a display interrupt; results are read from guest RAM. */
#include <atari.h>
#include <stdint.h>
#include "fujinet-nio.h"

extern void __fastcall__ traffic_dli(void);
extern volatile uint8_t traffic_dli_count;
#define ITERATIONS 200
#define RESULT ((volatile uint8_t *)0x7000)
static uint16_t ticks(void)
{
    volatile uint8_t *clock = (volatile uint8_t *)0x13;
    uint8_t hi, lo;
    do { hi = clock[0]; lo = clock[1]; } while (hi != clock[0]);
    return ((uint16_t)hi << 8) | lo;
}
int main(void)
{
    uint8_t *dl = (uint8_t *)OS.sdlst;
    uint8_t old_dli = dl[15];
    void (*old_vector)(void) = OS.vdslst;
    unsigned int i;
    uint16_t before;
    uint8_t result, failures = 0, slow = 0;
    FN_TIME_T time_value;
    RESULT[0] = 0x42;
    RESULT[1] = 0;
    RESULT[2] = 0;
    RESULT[3] = 0;
    RESULT[4] = 0;
    OS.vdslst = traffic_dli;
    dl[15] |= 0x80;
    ANTIC.nmien = 0xc0;
    result = fn_init();
    RESULT[2] = result;
    if (result == FN_OK) {
        for (i = 0; i < ITERATIONS; ++i) {
            before = ticks();
            result = fn_clock_get(&time_value);
            if (result != FN_OK) ++failures;
            if ((uint16_t)(ticks() - before) > 100) ++slow;
            RESULT[3] = (uint8_t)(i + 1);
        }
    }
    ANTIC.nmien = 0x40;
    dl[15] = old_dli;
    OS.vdslst = old_vector;
    RESULT[4] = failures;
    RESULT[5] = slow;
    RESULT[6] = traffic_dli_count;
    RESULT[1] = 0x5a;
    RESULT[0] = 0xa5;
    for (;;) {}
}
