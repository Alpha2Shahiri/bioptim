"""
This example uses the data from the balanced pendulum example to generate the data to track.
When it optimizes the program, contrary to the vanilla pendulum, it tracks the values instead of 'knowing' that
it is supposed to balance the pendulum. It is designed to show how to track marker and kinematic data.

Note that the final node is not tracked.
"""
import pytest
import importlib.util
from pathlib import Path

import numpy as np
from casadi import MX, SX, vertcat, sin
from bioptim import (
    BiorbdModel,
    OptimalControlProgram,
    ObjectiveList,
    ObjectiveFcn,
    DynamicsList,
    BoundsList,
    OdeSolver,
    OdeSolverBase,
    NonLinearProgram,
    ConfigureProblem,
    DynamicsFunctions,
    DynamicsEvaluation,
    InitialGuessList,
    ConstraintList,
    ConstraintFcn,
    Node,
)

# Load track_segment_on_rt
EXAMPLES_FOLDER = Path(__file__).parent
spec = importlib.util.spec_from_file_location("data_to_track", str(EXAMPLES_FOLDER)[:-5] + "bioptim/examples/getting_started/pendulum.py")
data_to_track = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_to_track)


def custom_configure(ocp: OptimalControlProgram, nlp: NonLinearProgram):
    """
    Tell the program which variables are states and controls.
    The user is expected to use the ConfigureProblem.configure_xxx functions.

    Parameters
    ----------
    ocp: OptimalControlProgram
        A reference to the ocp
    nlp: NonLinearProgram
        A reference to the phase
    """

    ConfigureProblem.configure_q(ocp, nlp, as_states=True, as_controls=False)
    ConfigureProblem.configure_qdot(ocp, nlp, as_states=True, as_controls=False)
    ConfigureProblem.configure_tau(ocp, nlp, as_states=False, as_controls=True)

    # name = "time"
    # name_t = [name]
    # ConfigureProblem.configure_new_variable(
    #     name,
    #     name_t,
    #     ocp,
    #     nlp,
    #     as_states=False,
    #     as_controls=False,
    #     as_states_dot=False,
    #     as_time=True,
    # )

    ConfigureProblem.configure_dynamics_function(ocp, nlp, time_dynamic)


def time_dynamic(
    time: MX | SX,
    states: MX | SX,
    controls: MX | SX,
    parameters: MX | SX,
    stochastic: MX | SX,
    nlp: NonLinearProgram,

) -> DynamicsEvaluation:
    """
    The custom dynamics function that provides the derivative of the states: dxdt = f(x, u, p)

    Parameters
    ----------
    states: MX | SX
        The state of the system
    controls: MX | SX
        The controls of the system
    parameters: MX | SX
        The parameters acting on the system
    nlp: NonLinearProgram
        A reference to the phase

    Returns
    -------
    The derivative of the states in the tuple[MX | SX] format
    """

    q = DynamicsFunctions.get(nlp.states["q"], states)
    qdot = DynamicsFunctions.get(nlp.states["qdot"], states)
    tau = DynamicsFunctions.get(nlp.controls["tau"], controls) + sin(time) * time.ones(nlp.model.nb_tau)

    # You can directly call biorbd function (as for ddq) or call bioptim accessor (as for dq)
    dq = DynamicsFunctions.compute_qdot(nlp, q, qdot)
    ddq = nlp.model.forward_dynamics(q, qdot, tau)

    # the user has to choose if want to return the explicit dynamics dx/dt = f(x,u,p)
    # as the first argument of DynamicsEvaluation or
    # the implicit dynamics f(x,u,p,xdot)=0 as the second argument
    # which may be useful for IRK or COLLOCATION integrators
    return DynamicsEvaluation(dxdt=vertcat(dq, ddq), defects=None)


# def configure_dynamics_function(ocp, nlp, dyn_func, expand: bool = True):
#     """
#     Configure the dynamics of the system
#
#     Parameters
#     ----------
#     ocp: OptimalControlProgram
#         A reference to the ocp
#     nlp: NonLinearProgram
#         A reference to the phase
#     dyn_func: Callable[states, controls, param]
#         The function to get the derivative of the states
#     expand: bool
#         If the dynamics should be expanded with casadi
#     """
#
#     nlp.parameters = ocp.parameters
#     DynamicsFunctions.apply_parameters(nlp.parameters.mx, nlp)
#
#     dynamics_eval = dyn_func(
#         ocp.nlp[nlp.phase_idx].t0,
#         nlp.states.scaled.mx_reduced,
#         nlp.controls.scaled.mx_reduced,
#         nlp.parameters.mx,
#         nlp.stochastic_variables.mx,
#         nlp,
#     )
#
#     dynamics_dxdt = dynamics_eval.dxdt
#     if isinstance(dynamics_dxdt, (list, tuple)):
#         dynamics_dxdt = vertcat(*dynamics_dxdt)
#
#     nlp.dynamics_func = Function(
#         "ForwardDyn",
#         [
#             nlp.time.mx,
#             nlp.states.scaled.mx_reduced,
#             nlp.controls.scaled.mx_reduced,
#             nlp.parameters.mx,
#             nlp.stochastic_variables.mx,
#         ],
#         [dynamics_dxdt],
#         ["t", "x", "u", "p", "s"],
#         ["xdot"],
#     )
#
#     if expand:
#         nlp.dynamics_func = nlp.dynamics_func.expand()
#
#     if dynamics_eval.defects is not None:
#         nlp.implicit_dynamics_func = Function(
#             "DynamicsDefects",
#             [
#                 nlp.time.mx,
#                 nlp.states.scaled.mx_reduced,
#                 nlp.controls.scaled.mx_reduced,
#                 nlp.parameters.mx,
#                 nlp.stochastic_variables.mx,
#                 nlp.states_dot.scaled.mx_reduced,
#             ],
#             [dynamics_eval.defects],
#             ["t", "x", "u", "p", "s", "xdot"],
#             ["defects"],
#         ).expand()

def prepare_ocp(
    bio_model: list[BiorbdModel],
    final_time: float,
    n_shooting: list[int],
    ode_solver: OdeSolverBase = OdeSolver.RK4(n_integration_steps=5),
    assume_phase_dynamics: bool = False,
) -> OptimalControlProgram:
    """
    Prepare the ocp

    Parameters
    ----------
    bio_model: BiorbdModel
        The loaded biorbd model
    final_time: float
        The time at final node
    n_shooting: int
        The number of shooting points
    markers_ref: np.ndarray
        The markers to track
    tau_ref: np.ndarray
        The generalized forces to track
    ode_solver: OdeSolverBase
        The ode solver to use
    assume_phase_dynamics: bool
        If the dynamics equation within a phase is unique or changes at each node. True is much faster, but lacks the
        capability to have changing dynamics within a phase. A good example of when False should be used is when
        different external forces are applied at each node

    Returns
    -------
    The OptimalControlProgram ready to be solved
    """
    # Add objective functions
    objective_functions = ObjectiveList()
    for i in range(len(bio_model)):
        objective_functions.add(ObjectiveFcn.Lagrange.MINIMIZE_CONTROL, key="tau", weight=100, phase=i)

    # Dynamics
    dynamics = DynamicsList()
    expand = False if isinstance(ode_solver, OdeSolver.IRK) else True
    for i in range(len(bio_model)):
        dynamics.add(custom_configure, dynamic_function=time_dynamic, phase=i, expand=expand)

    x_bounds = BoundsList()
    for i in range(len(bio_model)):
        x_bounds.add("q", bounds=bio_model[i].bounds_from_ranges("q"), phase=i)
        x_bounds.add("qdot", bounds=bio_model[i].bounds_from_ranges("qdot"), phase=i)

    # Define control path constraint
    tau_min, tau_max = -100, 100
    u_bounds = BoundsList()
    for i in range(len(bio_model)):
        u_bounds.add("tau", min_bound=[tau_min] * bio_model[i].nb_tau, max_bound=[tau_max] * bio_model[i].nb_tau, phase=i)

    x_init = InitialGuessList()
    u_init = InitialGuessList()
    for i in range(len(bio_model)):
        x_init.add(key="q", initial_guess=[1.57, 1.57], phase=i)
        x_init.add(key="qdot", initial_guess=[0, 0], phase=i)
        u_init.add(key="muscles", initial_guess=[0, 0], phase=i)

    return OptimalControlProgram(
        bio_model,
        dynamics,
        n_shooting,
        final_time,
        x_bounds=x_bounds,
        u_bounds=u_bounds,
        x_init=x_init,
        u_init=u_init,
        ode_solver=ode_solver,
        assume_phase_dynamics=assume_phase_dynamics,
    )


@pytest.mark.parametrize("nb_phase", [
    1,
    2,
])
def test_time_dependent_problem(nb_phase):
    """
    Firstly, it solves the getting_started/pendulum.py example. Afterward, it gets the marker positions and joint
    torque from the solution and uses them to track. It then creates and solves this ocp and show the results
    """

    biorbd_path = str(EXAMPLES_FOLDER)[:-5] + "bioptim/examples/getting_started/models/pendulum.bioMod"
    bio_model = BiorbdModel(biorbd_path)
    bio_model = [bio_model] * nb_phase
    final_time = [1] * nb_phase
    n_shooting = [20] * nb_phase

    ocp = prepare_ocp(
        bio_model,
        final_time=final_time,
        n_shooting=n_shooting,
    )

    # --- Solve the program --- #
    sol = ocp.solve()
    # sol.graphs()
