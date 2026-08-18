# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

import numpy as np
cimport numpy as np
from libc.math cimport sin, cos, fabs

def solve_kepler_vectorized(
    np.ndarray[np.float64_t, ndim=1] M,
    np.ndarray[np.float64_t, ndim=1] e,
    double tol=1e-12,
    int max_iter=50
):
    """
    Cython optimized Kepler solver that releases the GIL.
    Computes E for M = E - e*sin(E).
    """
    cdef Py_ssize_t n = M.shape[0]
    cdef np.ndarray[np.float64_t, ndim=1] E = np.empty(n, dtype=np.float64)

    cdef double[:] M_view = M
    cdef double[:] e_view = e
    cdef double[:] E_view = E

    cdef Py_ssize_t i
    cdef int iter_count
    cdef double f, f_prime, delta_E
    cdef int converged

    with nogil:
        for i in range(n):
            E_view[i] = M_view[i]
            converged = 0
            for iter_count in range(max_iter):
                f = E_view[i] - e_view[i] * sin(E_view[i]) - M_view[i]
                f_prime = 1.0 - e_view[i] * cos(E_view[i])

                if f_prime < 1e-12:
                    f_prime = 1e-12

                delta_E = f / f_prime
                E_view[i] = E_view[i] - delta_E

                if fabs(delta_E) < tol:
                    converged = 1
                    break

            if converged == 0:
                with gil:
                    raise Exception(f"Kepler solver did not converge for index {i} after {max_iter} iterations.")

    return E
