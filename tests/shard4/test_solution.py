import os

import pytest
import numpy as np
from bioptim import Shooting, OdeSolver, SolutionIntegrator, Solver, ControlType, PhaseDynamics, SolutionMerge


@pytest.mark.parametrize("phase_dynamics", [PhaseDynamics.SHARED_DURING_THE_PHASE, PhaseDynamics.ONE_PER_NODE])
@pytest.mark.parametrize("ode_solver", [OdeSolver.RK4, OdeSolver.COLLOCATION])
def test_time(ode_solver, phase_dynamics):
    # Load pendulum
    from bioptim.examples.getting_started import pendulum as ocp_module

    bioptim_folder = os.path.dirname(ocp_module.__file__)

    ocp = ocp_module.prepare_ocp(
        biorbd_model_path=bioptim_folder + "/models/pendulum.bioMod",
        final_time=2,
        n_shooting=10,
        ode_solver=ode_solver(),
        phase_dynamics=phase_dynamics,
        expand_dynamics=True,
    )
    solver = Solver.IPOPT(show_online_optim=False)
    solver.set_maximum_iterations(0)
    solver.set_print_level(0)

    sol = ocp.solve(solver=solver)
    time = sol.decision_time(to_merge=SolutionMerge.NODES)
    if ode_solver == OdeSolver.RK4:
        np.testing.assert_almost_equal(time.shape, (22, 1))
        np.testing.assert_almost_equal(time[0], 0)
        np.testing.assert_almost_equal(time[-1], 2)
        np.testing.assert_almost_equal(time[8], 0.8)
    else:
        np.testing.assert_almost_equal(time.shape, (61, 1))
        np.testing.assert_almost_equal(time[0], 0)
        np.testing.assert_almost_equal(time[-1], 2)
        np.testing.assert_almost_equal(time[4], 0.18611363115940527)


@pytest.mark.parametrize("phase_dynamics", [PhaseDynamics.SHARED_DURING_THE_PHASE, PhaseDynamics.ONE_PER_NODE])
@pytest.mark.parametrize("ode_solver", [OdeSolver.RK4, OdeSolver.COLLOCATION])
@pytest.mark.parametrize("continuous", [True, False])
def test_time_multiphase(ode_solver, phase_dynamics, continuous):
    # Load slider
    from bioptim.examples.torque_driven_ocp import slider as ocp_module

    bioptim_folder = os.path.dirname(ocp_module.__file__)

    ocp = ocp_module.prepare_ocp(
        biorbd_model_path=bioptim_folder + "/models/slider.bioMod",
        ode_solver=ode_solver(),
        phase_time=(0.2, 0.3, 0.5),
        n_shooting=(3, 4, 5),
        phase_dynamics=phase_dynamics,
        expand_dynamics=True,
    )

    solver = Solver.IPOPT(show_online_optim=False)
    solver.set_maximum_iterations(0)
    solver.set_print_level(0)

    sol = ocp.solve(solver=solver)

    time = sol.decision_time(to_merge=SolutionMerge.NODES, continuous=continuous)
    np.testing.assert_almost_equal(len(time), 3)

    if continuous:
        if ode_solver == OdeSolver.RK4:
            np.testing.assert_almost_equal(len(time[0]), 8)
            np.testing.assert_almost_equal(len(time[1]), 10)
            np.testing.assert_almost_equal(len(time[2]), 12)
            np.testing.assert_almost_equal(time[0][0], 0)
            np.testing.assert_almost_equal(time[0][-1], 0.2)
            np.testing.assert_almost_equal(time[1][0], 0.2)
            np.testing.assert_almost_equal(time[1][-1], 0.5)
            np.testing.assert_almost_equal(time[2][0], 0.5)
            np.testing.assert_almost_equal(time[2][-1], 1)
            np.testing.assert_almost_equal(time[2][6], 0.8)

        else:
            np.testing.assert_almost_equal(len(time[0]), 19)
            np.testing.assert_almost_equal(len(time[1]), 25)
            np.testing.assert_almost_equal(len(time[2]), 31)
            np.testing.assert_almost_equal(time[0][0], 0)
            np.testing.assert_almost_equal(time[0][-1], 0.2)
            np.testing.assert_almost_equal(time[1][0], 0.2)
            np.testing.assert_almost_equal(time[1][-1], 0.5)
            np.testing.assert_almost_equal(time[2][0], 0.5)
            np.testing.assert_almost_equal(time[2][-1], 1)
            np.testing.assert_almost_equal(time[2][3], 0.5669990521792428)
    else:
        if ode_solver == OdeSolver.RK4:
            np.testing.assert_almost_equal(len(time[0]), 8)
            np.testing.assert_almost_equal(len(time[1]), 10)
            np.testing.assert_almost_equal(len(time[2]), 12)
            np.testing.assert_almost_equal(time[0][0], 0)
            np.testing.assert_almost_equal(time[0][-1], 0.2)
            np.testing.assert_almost_equal(time[1][0], 0)
            np.testing.assert_almost_equal(time[1][-1], 0.3)
            np.testing.assert_almost_equal(time[2][0], 0)
            np.testing.assert_almost_equal(time[2][-1], 0.5)
            np.testing.assert_almost_equal(time[2][3], 0.2)

        else:
            np.testing.assert_almost_equal(len(time[0]), 19)
            np.testing.assert_almost_equal(len(time[1]), 25)
            np.testing.assert_almost_equal(len(time[2]), 31)
            np.testing.assert_almost_equal(time[0][0], 0)
            np.testing.assert_almost_equal(time[0][-1], 0.2)
            np.testing.assert_almost_equal(time[1][0], 0)
            np.testing.assert_almost_equal(time[1][-1], 0.3)
            np.testing.assert_almost_equal(time[2][0], 0)
            np.testing.assert_almost_equal(time[2][-1], 0.5)
            np.testing.assert_almost_equal(time[2][3], 0.0669990521792428)


@pytest.mark.parametrize("phase_dynamics", [PhaseDynamics.SHARED_DURING_THE_PHASE, PhaseDynamics.ONE_PER_NODE])
@pytest.mark.parametrize("ode_solver", [OdeSolver.RK4, OdeSolver.COLLOCATION])
@pytest.mark.parametrize("merge_phase", [True, False])
@pytest.mark.parametrize("continuous", [True, False])
def test_generate_stepwise_time(ode_solver, merge_phase, phase_dynamics, continuous):
    # Load slider
    from bioptim.examples.torque_driven_ocp import slider as ocp_module

    bioptim_folder = os.path.dirname(ocp_module.__file__)

    ocp = ocp_module.prepare_ocp(
        biorbd_model_path=bioptim_folder + "/models/slider.bioMod",
        ode_solver=ode_solver(),
        phase_time=(0.2, 0.3, 0.5),
        n_shooting=(3, 4, 5),
        phase_dynamics=phase_dynamics,
        expand_dynamics=True,
    )

    solver = Solver.IPOPT(show_online_optim=False)
    solver.set_maximum_iterations(0)
    solver.set_print_level(0)

    sol = ocp.solve(solver=solver)

    time = sol.stepwise_time(
        to_merge=[SolutionMerge.NODES, SolutionMerge.PHASES if merge_phase else None],
        continuous=continuous,
    )

    if continuous:
        if merge_phase:
            np.testing.assert_almost_equal(time[0], 0)
            np.testing.assert_almost_equal(time[-1], 1)
            np.testing.assert_equal(time.shape, (75, 1))
            if ode_solver == OdeSolver.RK4:
                np.testing.assert_almost_equal(time[4], 0.05333333333333334)
                np.testing.assert_almost_equal(time[30], 0.35)
                np.testing.assert_almost_equal(time[56], 0.7)
            else:
                np.testing.assert_almost_equal(time[4], 0.06203787705313508)
                np.testing.assert_almost_equal(time[30], 0.35)
                np.testing.assert_almost_equal(time[56], 0.7)

        else:
            np.testing.assert_almost_equal(time[0][0], 0)
            np.testing.assert_almost_equal(time[-1][-1], 1)
            np.testing.assert_equal(time[0].shape, (19, 1))
            np.testing.assert_equal(time[1].shape, (25, 1))
            np.testing.assert_equal(time[2].shape, (31, 1))
            if ode_solver == OdeSolver.RK4:
                np.testing.assert_almost_equal(time[0][4], 0.05333333333333334)
                np.testing.assert_almost_equal(time[1][4], 0.26)
                np.testing.assert_almost_equal(time[2][4], 0.5800000000000001)
            else:
                np.testing.assert_almost_equal(time[0][4], 0.06203787705313508)
                np.testing.assert_almost_equal(time[1][4], 0.269792611684777)
                np.testing.assert_almost_equal(time[2][4], 0.5930568155797027)
    else:
        if merge_phase:
            np.testing.assert_almost_equal(time[0], 0)
            np.testing.assert_almost_equal(time[-1], 0.5)
            np.testing.assert_equal(time.shape, (75, 1))
            if ode_solver == OdeSolver.RK4:
                np.testing.assert_almost_equal(time[4], 0.05333333333333334)
                np.testing.assert_almost_equal(time[30], 0.15)
                np.testing.assert_almost_equal(time[56], 0.2)
            else:
                np.testing.assert_almost_equal(time[4], 0.06203787705313508)
                np.testing.assert_almost_equal(time[30], 0.15)
                np.testing.assert_almost_equal(time[56], 0.2)

        else:
            np.testing.assert_almost_equal(time[0][0], 0)
            np.testing.assert_almost_equal(time[-1][-1], 0.5)
            np.testing.assert_equal(time[0].shape, (19, 1))
            np.testing.assert_equal(time[1].shape, (25, 1))
            np.testing.assert_equal(time[2].shape, (31, 1))
            if ode_solver == OdeSolver.RK4:
                np.testing.assert_almost_equal(time[0][4], 0.05333333333333334)
                np.testing.assert_almost_equal(time[1][4], 0.06)
                np.testing.assert_almost_equal(time[2][4], 0.0800000000000001)
            else:
                np.testing.assert_almost_equal(time[0][4], 0.06203787705313508)
                np.testing.assert_almost_equal(time[1][4], 0.069792611684777)
                np.testing.assert_almost_equal(time[2][4], 0.0930568155797027)


@pytest.mark.parametrize("phase_dynamics", [PhaseDynamics.SHARED_DURING_THE_PHASE, PhaseDynamics.ONE_PER_NODE])
@pytest.mark.parametrize("ode_solver", [OdeSolver.RK4, OdeSolver.COLLOCATION])
@pytest.mark.parametrize("merge_phase", [True, False])
@pytest.mark.parametrize("continuous", [True, False])
def test_generate_decision_time(ode_solver, merge_phase, phase_dynamics, continuous):
    # Load slider
    from bioptim.examples.torque_driven_ocp import slider as ocp_module

    bioptim_folder = os.path.dirname(ocp_module.__file__)

    ocp = ocp_module.prepare_ocp(
        biorbd_model_path=bioptim_folder + "/models/slider.bioMod",
        ode_solver=ode_solver(),
        phase_time=(0.2, 0.3, 0.5),
        n_shooting=(3, 4, 5),
        phase_dynamics=phase_dynamics,
        expand_dynamics=True,
    )

    solver = Solver.IPOPT(show_online_optim=False)
    solver.set_maximum_iterations(0)
    solver.set_print_level(0)

    sol = ocp.solve(solver=solver)

    time = sol.decision_time(
        to_merge=[SolutionMerge.NODES, SolutionMerge.PHASES if merge_phase else None],
        continuous=continuous,
    )

    if continuous:
        if merge_phase:
            np.testing.assert_almost_equal(time[0], 0)
            np.testing.assert_almost_equal(time[-1], 1)
            if ode_solver == OdeSolver.RK4:
                np.testing.assert_equal(time.shape, (30, 1))
                np.testing.assert_almost_equal(time[4], 0.13333333333)
                np.testing.assert_almost_equal(time[13], 0.425)
                np.testing.assert_almost_equal(time[29], 1.0)
            else:
                np.testing.assert_equal(time.shape, (75, 1))
                np.testing.assert_almost_equal(time[4], 0.06203787705313508)
                np.testing.assert_almost_equal(time[30], 0.35)
                np.testing.assert_almost_equal(time[56], 0.7)

        else:
            np.testing.assert_almost_equal(time[0][0], 0)
            np.testing.assert_almost_equal(time[-1][-1], 1)
            if ode_solver == OdeSolver.RK4:
                np.testing.assert_equal(time[0].shape, (8, 1))
                np.testing.assert_equal(time[1].shape, (10, 1))
                np.testing.assert_equal(time[2].shape, (12, 1))
                np.testing.assert_almost_equal(time[0][4], 0.13333333333)
                np.testing.assert_almost_equal(time[1][4], 0.35)
                np.testing.assert_almost_equal(time[2][4], 0.7)
            else:
                np.testing.assert_equal(time[0].shape, (19, 1))
                np.testing.assert_equal(time[1].shape, (25, 1))
                np.testing.assert_equal(time[2].shape, (31, 1))
                np.testing.assert_almost_equal(time[0][4], 0.06203787705313508)
                np.testing.assert_almost_equal(time[1][4], 0.269792611684777)
                np.testing.assert_almost_equal(time[2][4], 0.5930568155797027)
    else:
        if merge_phase:
            np.testing.assert_almost_equal(time[0], 0)
            np.testing.assert_almost_equal(time[-1], 0.5)
            if ode_solver == OdeSolver.RK4:
                np.testing.assert_equal(time.shape, (30, 1))
                np.testing.assert_almost_equal(time[4], 0.13333333333)
                np.testing.assert_almost_equal(time[13], 0.225)
                np.testing.assert_almost_equal(time[29], 0.5)
            else:
                np.testing.assert_equal(time.shape, (75, 1))
                np.testing.assert_almost_equal(time[4], 0.06203787705313508)
                np.testing.assert_almost_equal(time[30], 0.15)
                np.testing.assert_almost_equal(time[56], 0.2)

        else:
            np.testing.assert_almost_equal(time[0][0], 0)
            np.testing.assert_almost_equal(time[-1][-1], 0.5)
            if ode_solver == OdeSolver.RK4:
                np.testing.assert_equal(time[0].shape, (8, 1))
                np.testing.assert_equal(time[1].shape, (10, 1))
                np.testing.assert_equal(time[2].shape, (12, 1))
                np.testing.assert_almost_equal(time[0][4], 0.13333333333)
                np.testing.assert_almost_equal(time[1][4], 0.15)
                np.testing.assert_almost_equal(time[2][4], 0.2)
            else:
                np.testing.assert_equal(time[0].shape, (19, 1))
                np.testing.assert_equal(time[1].shape, (25, 1))
                np.testing.assert_equal(time[2].shape, (31, 1))
                np.testing.assert_almost_equal(time[0][4], 0.06203787705313508)
                np.testing.assert_almost_equal(time[1][4], 0.069792611684777)
                np.testing.assert_almost_equal(time[2][4], 0.0930568155797027)


@pytest.mark.parametrize("phase_dynamics", [PhaseDynamics.SHARED_DURING_THE_PHASE, PhaseDynamics.ONE_PER_NODE])
@pytest.mark.parametrize("ode_solver", [OdeSolver.RK4, OdeSolver.COLLOCATION])
@pytest.mark.parametrize("merge_phase", [True, False])
@pytest.mark.parametrize("shooting_type", [Shooting.SINGLE, Shooting.SINGLE_DISCONTINUOUS_PHASE, Shooting.MULTIPLE])
@pytest.mark.parametrize("integrator", [SolutionIntegrator.OCP, SolutionIntegrator.SCIPY_RK45])
@pytest.mark.parametrize("control_type", [ControlType.CONSTANT, ControlType.LINEAR_CONTINUOUS])
def test_generate_integrate(ode_solver, merge_phase, shooting_type, integrator, phase_dynamics, control_type):
    # Load slider
    from bioptim.examples.torque_driven_ocp import slider as ocp_module

    bioptim_folder = os.path.dirname(ocp_module.__file__)

    if ode_solver == OdeSolver.COLLOCATION and control_type == ControlType.LINEAR_CONTINUOUS:
        with pytest.raises(
            NotImplementedError, match="ControlType.LINEAR_CONTINUOUS ControlType not implemented yet with COLLOCATION"
        ):
            ocp = ocp_module.prepare_ocp(
                biorbd_model_path=bioptim_folder + "/models/slider.bioMod",
                ode_solver=ode_solver(),
                phase_time=(0.2, 0.3, 0.5),
                n_shooting=(3, 4, 5),
                phase_dynamics=phase_dynamics,
                control_type=control_type,
                expand_dynamics=True,
            )
        return

    ocp = ocp_module.prepare_ocp(
        biorbd_model_path=bioptim_folder + "/models/slider.bioMod",
        ode_solver=ode_solver(),
        phase_time=(0.2, 0.3, 0.5),
        n_shooting=(3, 4, 5),
        phase_dynamics=phase_dynamics,
        control_type=control_type,
        expand_dynamics=True,
    )

    solver = Solver.IPOPT(show_online_optim=False)
    solver.set_maximum_iterations(100)
    solver.set_print_level(0)
    sol = ocp.solve(solver=solver)

    if ode_solver == OdeSolver.COLLOCATION and integrator == SolutionIntegrator.OCP:
        with pytest.raises(
            ValueError,
            match="When the ode_solver of the Optimal Control Problem is OdeSolver.COLLOCATION, "
            "we cannot use the SolutionIntegrator.OCP.\n"
            "We must use one of the SolutionIntegrator provided by scipy with any Shooting Enum such as"
            " Shooting.SINGLE, Shooting.MULTIPLE, or Shooting.SINGLE_DISCONTINUOUS_PHASE",
        ):
            sol.integrate(
                shooting_type=shooting_type,
                to_merge=[SolutionMerge.NODES, SolutionMerge.PHASES if merge_phase else None],
                integrator=integrator,
            )
        return

    integrated_sol = sol.integrate(
        shooting_type=shooting_type,
        to_merge=[SolutionMerge.NODES, SolutionMerge.PHASES if merge_phase else None],
        integrator=integrator,
    )

    time = sol.stepwise_time(
        to_merge=[SolutionMerge.NODES, SolutionMerge.PHASES if merge_phase else None], continuous=True
    )

    if merge_phase:
        merged_sol = sol.stepwise_states(to_merge=[SolutionMerge.NODES, SolutionMerge.PHASES])
        np.testing.assert_equal(time.shape[0], merged_sol["q"][0, :].shape[0])
        np.testing.assert_almost_equal(time.shape[0], integrated_sol["q"][0, :].shape[0])
    else:
        for t, state in zip(time, integrated_sol):
            np.testing.assert_almost_equal(t.shape[0], state["q"][0, :].shape[0])

    if shooting_type == Shooting.SINGLE and merge_phase is False:
        np.testing.assert_almost_equal(integrated_sol[0]["q"][0, -1], integrated_sol[1]["q"][0, 0])
        np.testing.assert_almost_equal(integrated_sol[1]["q"][0, -1], integrated_sol[2]["q"][0, 0])

    import matplotlib.pyplot as plt

    plt.figure()

    if merge_phase:
        plt.plot(time, merged_sol["q"][0, :], label="merged", marker=".")

    else:
        for t, state in zip(time, integrated_sol):
            plt.plot(t, state["q"].T, label="integrated by bioptim", marker=".")

    plt.legend()
    plt.vlines(0.2, -1, 1, color="black", linestyle="--")
    plt.vlines(0.5, -1, 1, color="black", linestyle="--")

    plt.title(f" merged={merge_phase},\n" f" ode_solver={ode_solver},\n" f" integrator={integrator},\n")
    plt.rcParams["axes.titley"] = 1.0  # y is in axes-relative coordinates.
    plt.rcParams["axes.titlepad"] = -20
    # plt.show()
