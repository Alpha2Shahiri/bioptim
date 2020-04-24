import biorbd

from biorbd_optim import (
    Instant,
    OptimalControlProgram,
    ProblemType,
    ObjectiveFunction,
    Constraint,
    Bounds,
    QAndQDotBounds,
    InitialConditions,
    ShowResult,
)


def prepare_ocp(biorbd_model_path="eocarSym.bioMod", show_online_optim=False):
    # --- Options --- #
    # Model path
    biorbd_model = biorbd.Model(biorbd_model_path)

    # Problem parameters
    number_shooting_points = 30
    final_time = 2
    torque_min, torque_max, torque_init = -100, 100, 0

    # Add objective functions
    objective_functions = {"type": ObjectiveFunction.minimize_torque, "weight": 100}

    # Dynamics
    variable_type = ProblemType.torque_driven

    # Constraints
    constraints = (
        {"type": Constraint.Type.MARKERS_TO_MATCH, "instant": Instant.START, "first_marker": 0, "second_marker": 1,},
        {"type": Constraint.Type.MARKERS_TO_MATCH, "instant": Instant.END, "first_marker": 0, "second_marker": 2,},
        {"type": Constraint.Type.PROPORTIONAL_Q, "instant": Instant.ALL, "first_dof": 2, "second_dof": 3, "coef": -1,},
    )

    # Path constraint
    X_bounds = QAndQDotBounds(biorbd_model)
    for i in range(4, 8):
        X_bounds.first_node_min[i] = 0
        X_bounds.last_node_min[i] = 0
        X_bounds.first_node_max[i] = 0
        X_bounds.last_node_max[i] = 0

    # Initial guess
    X_init = InitialConditions([0] * (biorbd_model.nbQ() + biorbd_model.nbQdot()))

    # Define control path constraint
    U_bounds = Bounds([torque_min] * biorbd_model.nbQ(), [torque_max] * biorbd_model.nbQ(),)
    U_init = InitialConditions([torque_init] * biorbd_model.nbQ())

    # ------------- #

    return OptimalControlProgram(
        biorbd_model,
        variable_type,
        number_shooting_points,
        final_time,
        objective_functions,
        X_init,
        U_init,
        X_bounds,
        U_bounds,
        constraints,
        show_online_optim=show_online_optim,
    )


if __name__ == "__main__":
    ocp = prepare_ocp(show_online_optim=False)

    # --- Solve the program --- #
    sol = ocp.solve()

    # --- Show results --- #
    result = ShowResult(ocp, sol)
    result.graphs()
