# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from libc.math cimport exp
from libc.stdlib cimport malloc, free
from cpython.pycapsule cimport PyCapsule_New, PyCapsule_GetPointer
from scipy import LowLevelCallable

cdef struct IntegrandData:
    double R_sq
    double b_0
    double b_1
    double C_inv_00
    double C_inv_01
    double C_inv_10
    double C_inv_11
    double norm_factor

cdef double integrand_c(int n, double *xx, void *user_data) noexcept nogil:
    cdef IntegrandData *data = <IntegrandData *>user_data
    cdef double zeta = xx[0]
    cdef double xi = xx[1]

    if xi*xi + zeta*zeta > data.R_sq:
        return 0.0

    cdef double u0 = xi - data.b_0
    cdef double u1 = zeta - data.b_1

    cdef double v0 = u0 * data.C_inv_00 + u1 * data.C_inv_10
    cdef double v1 = u0 * data.C_inv_01 + u1 * data.C_inv_11

    cdef double exponent = -0.5 * (u0 * v0 + u1 * v1)
    return data.norm_factor * exp(exponent)

cdef void free_data(object capsule) noexcept:
    cdef void *data = PyCapsule_GetPointer(capsule, "integrand_data")
    if data != NULL:
        free(data)

def create_low_level_callable(double R_sq, double b_0, double b_1,
                              double C_inv_00, double C_inv_01,
                              double C_inv_10, double C_inv_11,
                              double norm_factor):
    """
    Creates a scipy.LowLevelCallable C-hook for Foster's risk integration.
    """
    cdef IntegrandData *data = <IntegrandData *>malloc(sizeof(IntegrandData))
    data.R_sq = R_sq
    data.b_0 = b_0
    data.b_1 = b_1
    data.C_inv_00 = C_inv_00
    data.C_inv_01 = C_inv_01
    data.C_inv_10 = C_inv_10
    data.C_inv_11 = C_inv_11
    data.norm_factor = norm_factor

    cdef object user_data_capsule = PyCapsule_New(<void *>data, "integrand_data", free_data)
    cdef object func_capsule = PyCapsule_New(<void *>integrand_c, "double (int, double *, void *)", NULL)

    return LowLevelCallable(func_capsule, user_data_capsule)
