/**********
Copyright 1990 Regents of the University of California.  All rights reserved.
Author: 1985 Thomas L. Quarles
Modified: 2001 AlansFixes
**********/

/*
 * NIiter(ckt,maxIter)
 *
 *  This subroutine performs the actual numerical iteration.
 *  It uses the sparse matrix stored in the circuit struct
 *  along with the matrix loading program, the load data, the
 *  convergence test function, and the convergence parameters
 */

#include "ngspice/ngspice.h"
#include "ngspice/trandefs.h"
#include "ngspice/cktdefs.h"
#include "ngspice/smpdefs.h"
#include "ngspice/sperror.h"
#include "ngspice/fteext.h"
#include "../../spicelib/devices/vbic/vbicdefs.h"

/* Limit the number of 'singular matrix' warnings */
static int msgcount = 0;
/* [VBIC_THERMAL_VECTOR_PROBE] once-emitted flag only; resolver/node state is
   local to each NIiter invocation (circuit-keyed by construction) */
static bool vtp_printed = FALSE;

/* NIiter() - return value is non-zero for convergence failure */

int
NIiter(CKTcircuit *ckt, int maxIter)
{
    double startTime, *OldCKTstate0 = NULL;
    int error, i, j;

    int iterno = 0;
    int ipass = 0;
    int vtp_tnode = -1;
    int vtp_armed = 0;
    bool iteration_captured = FALSE;
    double time_at_load = NAN;
    long mode_at_load = 0;
    double old_before_load = NAN, assembled_before_solve = NAN;
    double solved_after_solve = NAN, after_damping = NAN, old_after_swap = NAN;
#ifdef KLU
    /* [MNA_SNAPSHOT] per-invocation latches + saved event key; the snapshot
       id is process-stable (static sequence). postsolve is armed only after
       a successful sparse prefactor snapshot (SMPsnapshotMNA == 0). The
       event key is the accepted probe event (tnode 100, iterno 3, CKTtime 0,
       MODETRANOP|MODEINITFIX; run 14b0060c). The size passed to the helper
       is the largest valid equation index (int) ckt->CKTmaxEqNum - 1
       (cktinit.c:42 init 1; cktnewn.c:37 node->number = CKTmaxEqNum++;
       span.c alloc/copy CKTmaxEqNum elements; cktdump.c:42/cktnames.c:23
       publish CKTmaxEqNum - 1); the helper fails closed on size <= 0. */
    bool vtp_snap_pre_done = FALSE;
    bool vtp_snap_post_done = FALSE;
    double vtp_snap_time = NAN;
    long vtp_snap_mode = 0;
    long vtp_snap_id = 0;
    static long vtp_snap_seq = 0;
    const int vtp_snap_iter = 3;
#endif

    /* some convergence issues that get resolved by increasing max iter */
    if (maxIter < 100)
        maxIter = 100;

    if ((ckt->CKTmode & MODETRANOP) && (ckt->CKTmode & MODEUIC)) {
        SWAP(double *, ckt->CKTrhs, ckt->CKTrhsOld);
        error = CKTload(ckt);
        if (error)
            return(error);
        return(OK);
    }

#ifdef WANT_SENSE2
    if (ckt->CKTsenInfo) {
        error = NIsenReinit(ckt);
        if (error)
            return(error);
    }
#endif

    if (ckt->CKTniState & NIUNINITIALIZED) {
        error = NIreinit(ckt); /* always returns 0 */
        if (error) {
#ifdef STEPDEBUG
            printf("re-init returned error \n");
#endif
            return(error);
        }
    }

    /* [VBIC_THERMAL_VECTOR_PROBE] resolve target thermal node once per
       invocation, AFTER initialization (NIreinit may allocate the vectors);
       explicitly scoped to the normal solver path (not the MODETRANOP+MODEUIC
       early return) */
    if (!vtp_printed) {
        int vtp_type = CKTtypelook("VBIC");
        if (vtp_type >= 0 && ckt->CKTrhs && ckt->CKTrhsOld) {
            GENmodel *vtp_model;
            for (vtp_model = ckt->CKThead[vtp_type]; vtp_model;
                 vtp_model = vtp_model->GENnextModel) {
                GENinstance *vtp_inst;
                for (vtp_inst = vtp_model->GENinstances; vtp_inst;
                     vtp_inst = vtp_inst->GENnextInstance) {
                    if (vtp_inst->GENname &&
                        strcmp(vtp_inst->GENname,
                               "q.xdiv2.xqs_comp_s.qnpn13g2") == 0) {
                        vtp_tnode = ((VBICinstance *) vtp_inst)->VBICtempNode;
                        if (vtp_tnode > 0 && vtp_tnode < ckt->CKTmaxEqNum)
                            vtp_armed = 1;
                        break;
                    }
                }
                if (vtp_armed == 1)
                    break;
            }
        }
    }

    /* OldCKTstate0 = TMALLOC(double, ckt->CKTnumStates + 1); */

    for (;;) {
        old_before_load = NAN;
        assembled_before_solve = NAN;
        solved_after_solve = NAN;
        after_damping = NAN;
        old_after_swap = NAN;
        time_at_load = NAN;
        mode_at_load = 0;
        iteration_captured = FALSE;

        ckt->CKTnoncon = 0;

#ifdef NEWPRED
        if (!(ckt->CKTmode & MODEINITPRED))
#endif
        {

            if (vtp_armed == 1) {
                old_before_load = *(ckt->CKTrhsOld + vtp_tnode);
                time_at_load = ckt->CKTtime;
                mode_at_load = (long) ckt->CKTmode;
            }
            error = CKTload(ckt);
            /* printf("loaded, noncon is %d\n", ckt->CKTnoncon); */
            /* fflush(stdout); */
            iterno++;
            if (error) {
                ckt->CKTstat->STATnumIter += iterno;
#ifdef STEPDEBUG
                printf("load returned error \n");
#endif
                FREE(OldCKTstate0);
                return (error);
            }
#ifdef KLU
            /* [MNA_SNAPSHOT] pre-factor phase: once-only, immediately after
               CKTload and before any reorder/factor (SMPpreOrder, SMPreorder,
               SMPluFac below); saves the event key and arms postsolve only
               on a successful sparse prefactor (SMPsnapshotMNA == 0) */
            if (vtp_armed == 1 && !vtp_snap_pre_done &&
                iterno == vtp_snap_iter && ckt->CKTtime == 0.0 &&
                ((ckt->CKTmode & MODETRANOP) != 0) &&
                ((ckt->CKTmode & MODEINITFIX) != 0)) {
                const int vtp_snap_max_eq = (int) ckt->CKTmaxEqNum - 1;
                vtp_snap_time = ckt->CKTtime;
                vtp_snap_mode = (long) ckt->CKTmode;
                vtp_snap_id = ++vtp_snap_seq;
                if (SMPsnapshotMNA(ckt->CKTmatrix, ckt->CKTrhs,
                                   vtp_snap_max_eq, ckt->CKTkluMODE,
                                   "prefactor", vtp_snap_id, vtp_tnode,
                                   iterno, ckt->CKTtime,
                                   (long) ckt->CKTmode) == 0) {
                    /* [EQMAP] equation-index -> node-name rows for the 13
                     * target equations, INSIDE the same successful prefactor
                     * branch (once-only authority: the existing !vtp_snap_pre_done
                     * guard plus a successful SMPsnapshotMNA return); the records
                     * carry the existing dynamic vtp_snap_id (no hardcoded id).
                     * Read-only CKTnode walk from ckt->CKTnodes->next (ground
                     * excluded); stderr only; no matrix/RHS/state/node/device
                     * writes; no element creation. Structurally countable:
                     * BEGIN with event identity and expected count, exactly one
                     * [EQMAP] row per target equation, END with emitted count. */
                    const int eqmap_targets[13] = {
                        2, 70, 79, 98, 99, 100,
                        102, 103, 104, 105, 106, 107, 108};
                    CKTnode *eqmap_node;
                    int eqmap_i, eqmap_hit, eqmap_emitted = 0;
                    fprintf(stderr,
                            "[EQMAP_BEGIN] id=%ld tnode=%d iterno=%d time=%a mode=%ld expected=%d\n",
                            vtp_snap_id, vtp_tnode, iterno, ckt->CKTtime,
                            (long) ckt->CKTmode, 13);
                    for (eqmap_i = 0; eqmap_i < 13; eqmap_i++) {
                        eqmap_hit = 0;
                        for (eqmap_node = ckt->CKTnodes->next; eqmap_node;
                             eqmap_node = eqmap_node->next) {
                            if (eqmap_node->number == eqmap_targets[eqmap_i]) {
                                fprintf(stderr, "[EQMAP] id=%ld eq=%d name=%s\n",
                                        vtp_snap_id, eqmap_node->number,
                                        (eqmap_node->name != NULL)
                                            ? eqmap_node->name : "<null>");
                                eqmap_hit = 1;
                                break;
                            }
                        }
                        eqmap_emitted++;
                        if (!eqmap_hit)
                            fprintf(stderr, "[EQMAP] id=%ld eq=%d name=<absent>\n",
                                    vtp_snap_id, eqmap_targets[eqmap_i]);
                    }
                    fprintf(stderr, "[EQMAP_END] id=%ld emitted=%d expected=%d\n",
                            vtp_snap_id, eqmap_emitted, 13);
                    vtp_snap_pre_done = TRUE;
                }
            }
#endif

            /* printf("after loading, before solving\n"); */
            /* CKTdump(ckt); */

            if (!(ckt->CKTniState & NIDIDPREORDER)) {
                error = SMPpreOrder(ckt->CKTmatrix);
                if (error) {
                    ckt->CKTstat->STATnumIter += iterno;
#ifdef STEPDEBUG
                    printf("pre-order returned error \n");
#endif
                    FREE(OldCKTstate0);
                    return(error); /* badly formed matrix */
                }
                ckt->CKTniState |= NIDIDPREORDER;
            }

            if ((ckt->CKTmode & MODEINITJCT) ||
                ((ckt->CKTmode & MODEINITTRAN) && (iterno == 1)))
            {
                ckt->CKTniState |= NISHOULDREORDER;
            }

            if (ckt->CKTniState & NISHOULDREORDER) {
                startTime = SPfrontEnd->IFseconds();

#ifdef KLU
                if (ckt->CKTkluMODE) {
                    ckt->CKTmatrix->SMPkluMatrix->KLUloadDiagGmin = 1 ;
                }
#endif

                error = SMPreorder(ckt->CKTmatrix, ckt->CKTpivotAbsTol,
                                   ckt->CKTpivotRelTol, ckt->CKTdiagGmin);
                ckt->CKTstat->STATreorderTime +=
                    SPfrontEnd->IFseconds() - startTime;
                if (error) {
                    /* new feature - we can now find out something about what is
                     * wrong - so we ask for the troublesome entry
                     * Limit the number of messages to 6, if not 'set ngdebug'.
                     */
                    if (ft_ngdebug || msgcount < 6) {
                        SMPgetError(ckt->CKTmatrix, &i, &j);
                        if(eq(NODENAME(ckt, i), NODENAME(ckt, j)))
                            SPfrontEnd->IFerrorf(ERR_WARNING, "singular matrix:  check node %s\n", NODENAME(ckt, i));
                        else
                            SPfrontEnd->IFerrorf(ERR_WARNING, "singular matrix:  check nodes %s and %s\n", NODENAME(ckt, i), NODENAME(ckt, j));
                        msgcount += 1;
                    }
                    ckt->CKTstat->STATnumIter += iterno;
#ifdef STEPDEBUG
                    printf("reorder returned error \n");
#endif
                    FREE(OldCKTstate0);
                    return(error); /* can't handle these errors - pass up! */
                }
                ckt->CKTniState &= ~NISHOULDREORDER;
            } else {
                startTime = SPfrontEnd->IFseconds();

#ifdef KLU
                if (ckt->CKTkluMODE) {
                    ckt->CKTmatrix->SMPkluMatrix->KLUloadDiagGmin = 1 ;
                }
#endif

                error = SMPluFac(ckt->CKTmatrix, ckt->CKTpivotAbsTol,
                                 ckt->CKTdiagGmin);
                ckt->CKTstat->STATdecompTime +=
                    SPfrontEnd->IFseconds() - startTime;

#ifdef KLU
                if ((ckt->CKTkluMODE) && (error == E_SINGULAR)) {

                    /* Francesco Lannutti - 25 Aug 2020
                     * If the matrix is numerically singular during ReFactorization, take the same matrix and factor it from scratch in the same iteration.
                     * This is my mod with KLU. It saves run-time, but also the system at the next iteration may be different.
                     * How do we guarantee that the system is the same at the next iteration? So, the original SPARSE version below sounds like a bug.
                     */
                    if (ft_ngdebug)
                        fprintf (stderr, "Warning: KLU ReFactor failed. Factoring again...\n") ;
                    ckt->CKTniState |= NISHOULDREORDER;
                    ckt->CKTmatrix->SMPkluMatrix->KLUloadDiagGmin = 0 ;
                    error = SMPreorder(ckt->CKTmatrix, ckt->CKTpivotAbsTol, ckt->CKTpivotRelTol, ckt->CKTdiagGmin);
                    ckt->CKTstat->STATreorderTime += SPfrontEnd->IFseconds() - startTime;
                    if (error) {
                        SMPgetError(ckt->CKTmatrix, &i, &j);
                        if (ft_ngdebug || msgcount < 6) {
                            SMPgetError(ckt->CKTmatrix, &i, &j);
                            if (eq(NODENAME(ckt, i), NODENAME(ckt, j)))
                                SPfrontEnd->IFerrorf(ERR_WARNING, "singular matrix:  check node %s\n", NODENAME(ckt, i));
                            else
                                SPfrontEnd->IFerrorf(ERR_WARNING, "singular matrix:  check nodes %s and %s\n", NODENAME(ckt, i), NODENAME(ckt, j));
                            msgcount += 1;
                        }

                        /* CKTload(ckt); */
                        /* SMPprint(ckt->CKTmatrix, stdout); */
                        /* seems to be singular - pass the bad news up */
                        ckt->CKTstat->STATnumIter += iterno;
#ifdef STEPDEBUG
                        printf("lufac returned error \n");
#endif
                        FREE(OldCKTstate0);
                        return(error);
                    }
                } else if (error) {
                    if (!(ckt->CKTkluMODE) && (error == E_SINGULAR)) {

                        /* Francesco Lannutti - 25 Aug 2020
                         * If the matrix is numerically singular during ReFactorization, factor it from scratch at the next iteration.
                         * This is the original SPICE3F5 code and uses SPARSE.
                         */

                        ckt->CKTniState |= NISHOULDREORDER;
                        DEBUGMSG(" forced reordering....\n");
                        continue;
                    }
                    /* CKTload(ckt); */
                    /* SMPprint(ckt->CKTmatrix, stdout); */
                    /* seems to be singular - pass the bad news up */
                    ckt->CKTstat->STATnumIter += iterno;
#ifdef STEPDEBUG
                    printf("lufac returned error \n");
#endif
                    FREE(OldCKTstate0);
                    return(error);
                }
#else
                if (error) {
                    if (error == E_SINGULAR) {

                        /* Francesco Lannutti - 25 Aug 2020
                         * If the matrix is numerically singular during ReFactorization, factor it from scratch at the next iteration.
                         * This is the original SPICE3F5 code and uses SPARSE.
                         */

                        ckt->CKTniState |= NISHOULDREORDER;
                        DEBUGMSG(" forced reordering....\n");
                        continue;
                    }
                    /* CKTload(ckt); */
                    /* SMPprint(ckt->CKTmatrix, stdout); */
                    /* seems to be singular - pass the bad news up */
                    ckt->CKTstat->STATnumIter += iterno;
#ifdef STEPDEBUG
                    printf("lufac returned error \n");
#endif
                    FREE(OldCKTstate0);
                    return(error);
                }
#endif

            }

            /* moved it to here as if xspice is included then CKTload changes
               CKTnumStates the first time it is run */
            if (!OldCKTstate0)
                OldCKTstate0 = TMALLOC(double, ckt->CKTnumStates + 1);
            if (ckt->CKTstate0)
                memcpy(OldCKTstate0, ckt->CKTstate0,
                       (size_t) ckt->CKTnumStates * sizeof(double));

            startTime = SPfrontEnd->IFseconds();
            if (vtp_armed == 1)
                assembled_before_solve = *(ckt->CKTrhs + vtp_tnode);
            SMPsolve(ckt->CKTmatrix, ckt->CKTrhs, ckt->CKTrhsSpare);
            if (vtp_armed == 1) {
                solved_after_solve = *(ckt->CKTrhs + vtp_tnode);
                after_damping = solved_after_solve;
                iteration_captured = TRUE;
            }
#ifdef KLU
            /* [MNA_SNAPSHOT] post-solve phase: full solution vector, once-only,
               immediately after SMPsolve (before any damping); re-checks the
               exact saved event key (iterno/time/mode); if control left the
               keyed iteration before the solve (e.g., the sparse E_SINGULAR
               reorder-continue at base niiter.c:258), emit a fail-closed ABORT
               and never pair with a later solve */
            if (vtp_snap_pre_done && !vtp_snap_post_done) {
                const int vtp_snap_max_eq = (int) ckt->CKTmaxEqNum - 1;
                if (iterno == vtp_snap_iter && ckt->CKTtime == vtp_snap_time &&
                    (long) ckt->CKTmode == vtp_snap_mode) {
                    SMPsnapshotMNA(ckt->CKTmatrix, ckt->CKTrhs,
                                   vtp_snap_max_eq, ckt->CKTkluMODE,
                                   "postsolve", vtp_snap_id, vtp_tnode,
                                   iterno, ckt->CKTtime,
                                   (long) ckt->CKTmode);
                } else {
                    SMPsnapshotMNA(ckt->CKTmatrix, ckt->CKTrhs,
                                   vtp_snap_max_eq, ckt->CKTkluMODE,
                                   "abort", vtp_snap_id, vtp_tnode,
                                   vtp_snap_iter, vtp_snap_time,
                                   vtp_snap_mode);
                    vtp_snap_pre_done = FALSE;
                }
                vtp_snap_post_done = TRUE;
            }
#endif
            ckt->CKTstat->STATsolveTime +=
                SPfrontEnd->IFseconds() - startTime;
#ifdef STEPDEBUG
            /*XXXX*/
            if (ckt->CKTrhs[0] != 0.0)
                printf("NIiter: CKTrhs[0] = %g\n", ckt->CKTrhs[0]);
            if (ckt->CKTrhsSpare[0] != 0.0)
                printf("NIiter: CKTrhsSpare[0] = %g\n", ckt->CKTrhsSpare[0]);
            if (ckt->CKTrhsOld[0] != 0.0)
                printf("NIiter: CKTrhsOld[0] = %g\n", ckt->CKTrhsOld[0]);
            /*XXXX*/
#endif
            ckt->CKTrhs[0] = 0;
            ckt->CKTrhsSpare[0] = 0;
            ckt->CKTrhsOld[0] = 0;

            if (iterno > maxIter) {
                ckt->CKTstat->STATnumIter += iterno;
                /* we don't use this info during transient analysis */
                if (ckt->CKTcurrentAnalysis != DOING_TRAN) {
                    FREE(errMsg);
                    errMsg = copy("Too many iterations without convergence");
#ifdef STEPDEBUG
                    fprintf(stderr, "too many iterations without convergence: %d iter's (max iter == %d)\n",
                    iterno, maxIter);
#endif
                }
                FREE(OldCKTstate0);
                return(E_ITERLIM);
            }

            if ((ckt->CKTnoncon == 0) && (iterno != 1))
                ckt->CKTnoncon = NIconvTest(ckt);
            else
                ckt->CKTnoncon = 1;

#ifdef STEPDEBUG
            printf("noncon is %d\n", ckt->CKTnoncon);
#endif
        }

        if ((ckt->CKTnodeDamping != 0) && (ckt->CKTnoncon != 0) &&
            ((ckt->CKTmode & MODETRANOP) || (ckt->CKTmode & MODEDCOP)) &&
            (iterno > 1))
        {
            CKTnode *node;
            double diff, maxdiff = 0;
            for (node = ckt->CKTnodes->next; node; node = node->next)
                if (node->type == SP_VOLTAGE) {
                    diff = fabs(ckt->CKTrhs[node->number] - ckt->CKTrhsOld[node->number]);
                    if (maxdiff < diff)
                        maxdiff = diff;
                }

            if (maxdiff > 10) {
                double damp_factor = 10 / maxdiff;
                if (damp_factor < 0.1)
                    damp_factor = 0.1;
                for (node = ckt->CKTnodes->next; node; node = node->next) {
                    diff = ckt->CKTrhs[node->number] - ckt->CKTrhsOld[node->number];
                    ckt->CKTrhs[node->number] =
                        ckt->CKTrhsOld[node->number] + (damp_factor * diff);
                }
                for (i = 0; i < ckt->CKTnumStates; i++) {
                    diff = ckt->CKTstate0[i] - OldCKTstate0[i];
                    ckt->CKTstate0[i] = OldCKTstate0[i] + (damp_factor * diff);
                }
            }
        }
        if (vtp_armed == 1 && iteration_captured)
            after_damping = *(ckt->CKTrhs + vtp_tnode);

        if (ckt->CKTmode & MODEINITFLOAT) {
            if ((ckt->CKTmode & MODEDC) && ckt->CKThadNodeset) {
                if (ipass)
                    ckt->CKTnoncon = ipass;
                ipass = 0;
            }
            if (ckt->CKTnoncon == 0) {
                ckt->CKTstat->STATnumIter += iterno;
                FREE(OldCKTstate0);
                return(OK);
            }
        } else if (ckt->CKTmode & MODEINITJCT) {
            ckt->CKTmode = (ckt->CKTmode & ~INITF) | MODEINITFIX;
            ckt->CKTniState |= NISHOULDREORDER;
        } else if (ckt->CKTmode & MODEINITFIX) {
            if (ckt->CKTnoncon == 0)
                ckt->CKTmode = (ckt->CKTmode & ~INITF) | MODEINITFLOAT;
            ipass = 1;
        } else if (ckt->CKTmode & MODEINITSMSIG) {
            ckt->CKTmode = (ckt->CKTmode & ~INITF) | MODEINITFLOAT;
        } else if (ckt->CKTmode & MODEINITTRAN) {
            if (iterno <= 1)
                ckt->CKTniState |= NISHOULDREORDER;
            ckt->CKTmode = (ckt->CKTmode & ~INITF) | MODEINITFLOAT;
        } else if (ckt->CKTmode & MODEINITPRED) {
            ckt->CKTmode = (ckt->CKTmode & ~INITF) | MODEINITFLOAT;
        } else {
            ckt->CKTstat->STATnumIter += iterno;
#ifdef STEPDEBUG
            printf("bad initf state \n");
#endif
            FREE(OldCKTstate0);
            return(E_INTERN);
            /* impossible - no such INITF flag! */
        }

        /* build up the lvnim1 array from the lvn array */
        SWAP(double *, ckt->CKTrhs, ckt->CKTrhsOld);
        if (vtp_armed == 1 && iteration_captured) {
            old_after_swap = *(ckt->CKTrhsOld + vtp_tnode);
            if (!vtp_printed &&
                ((isfinite(old_before_load) && old_before_load < 0.0) ||
                 (isfinite(assembled_before_solve) && assembled_before_solve < 0.0) ||
                 (isfinite(solved_after_solve) && solved_after_solve < 0.0) ||
                 (isfinite(after_damping) && after_damping < 0.0) ||
                 (isfinite(old_after_swap) && old_after_swap < 0.0))) {
                fprintf(stderr, "\n[VBIC_THERMAL_VECTOR_PROBE] Instance: q.xdiv2.xqs_comp_s.qnpn13g2 | tnode: %d | iterno: %d | CKTtime_at_load: %g | CKTmode_at_load: %ld\n",
                        vtp_tnode, iterno, time_at_load, mode_at_load);
                fprintf(stderr, "  old_before_load: %a (isfinite=%d) | assembled_before_solve: %a (isfinite=%d) | solved_after_solve: %a (isfinite=%d) | after_damping: %a (isfinite=%d) | old_after_swap: %a (isfinite=%d)\n",
                        old_before_load, isfinite(old_before_load) ? 1 : 0,
                        assembled_before_solve, isfinite(assembled_before_solve) ? 1 : 0,
                        solved_after_solve, isfinite(solved_after_solve) ? 1 : 0,
                        after_damping, isfinite(after_damping) ? 1 : 0,
                        old_after_swap, isfinite(old_after_swap) ? 1 : 0);
                vtp_printed = TRUE;
            }
        }
        /* printf("after loading, after solving\n"); */
        /* CKTdump(ckt); */
    }
    /*NOTREACHED*/
}

void NIresetwarnmsg(void) {
    msgcount = 0;
}
