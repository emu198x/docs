/* Compile the unmodified reference ctc.c; only diagnostic and CPU IRQ sinks
 * are supplied here. This tests CTC semantics, not MEMU's full scheduler. */
#include <stdio.h>
#include <stdlib.h>
#include "ctc.h"
static unsigned raised;
void diag_message(unsigned int flag, const char *fmt, ...) { (void)flag; (void)fmt; }
void RaiseInt(const char *source) { (void)source; ++raised; }
int main(void) {
    const unsigned bases[] = {0, 0x20, 0x78, 0xf8};
    puts("base,event,counter,irq_raised,vector,reti");
    for (unsigned b = 0; b < 4; ++b) {
        ctc_init(); raised = 0;
        ctc_out(0, bases[b]); ctc_out(0, 0xc5); ctc_out(0, 1);
        for (unsigned event = 1; event <= 2; ++event) {
            ctc_trigger(0);
            word vector = 0xffff;
            if (!ctc_int_ack(&vector) || vector != bases[b]) return EXIT_FAILURE;
            int reti = ctc_reti();
            if (!reti || raised != event || ctc_in(0) != 1) return EXIT_FAILURE;
            printf("%u,%u,%u,%u,%u,%d\n", bases[b],event,ctc_in(0),raised,vector,reti);
        }
    }
    return EXIT_SUCCESS;
}
