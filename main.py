from argparse import ArgumentParser
import copy

STEP_CNT = 0
OUTPUT = []


def parse_var(var_file):
    with open(var_file, "r") as f:
        lines = f.readlines()
    var = list(map(lambda line: line.strip(), lines))
    return {item.split(":")[0]: list(map(int, item.split(":")[1].split())) for item in var}


def parse_con(constraint_file):
    with open(constraint_file, "r") as f:
        lines = f.readlines()
        return list(map(lambda line: line.strip(), lines))


def print_stdout(solution, status):
    global STEP_CNT, OUTPUT
    STEP_CNT += 1
    s = f"{STEP_CNT}. {', '.join(solution)}  {status}"
    OUTPUT.append(s)
    print(s)


def select_variable(csp, solution):
    domain_length = {k: len(v)
                     for k, v in csp["variables"].items()
                     if k not in solution.keys()}
    min_keys = [key for key, value in domain_length.items()
                if value == min(domain_length.values())]
    if len(min_keys) == 1:
        return min_keys[0]

    constraint_count = {k: 0 for k in min_keys}
    for constraint in csp["constraints"]:
        literals = constraint.split()
        if literals[0] in solution or literals[-1] in solution:
            continue
        for lit in literals:
            if lit.isalpha() and lit in min_keys:
                if lit in constraint_count:
                    constraint_count[lit] += 1
    if len(constraint_count):
        return max(constraint_count.keys(), key=lambda k: constraint_count[k])[0]
    return min_keys[0]


def select_value(csp, var, solution):
    values = {k: 0 for k in csp["variables"][var]}
    constraints = list(set([c for c in csp["constraints"]
                            for v in csp["variables"]
                            if v in c and var in c and v not in solution]))
    for constraint in constraints:
        var1, op, var2 = constraint.split(" ")
        if var1 in solution or var2 in solution:
            continue
        if var1 == var:
            adj = var2
            adj_values = csp["variables"][var2]
        else:
            adj = var1
            adj_values = csp["variables"][var1]
        if adj not in solution:
            for v in values:
                for av in adj_values:
                    csp["constraints"] = [constraint]
                    if constraint_satisfied({adj: av},
                                               csp, var, v, solution_str=[],
                                               stdout=False):
                        values[v] += 1
                    csp["constraints"] = csp["constraints_org"]
    sorted_keys = sorted(values.keys(), key=lambda x: (-values[x], x))
    sorted_dict = {k: values[k] for k in sorted_keys}
    v = list(sorted_dict.keys())
    return v


def forward_check(csp, solution):
    variables = [v for v in csp["variables"] if v not in list(solution.keys())]
    csp1 = copy.deepcopy(csp)
    for var in variables:
        constraints = list(set([c for c in csp["constraints"]
                                for v in solution
                                if v in c and var in c]))
        for constraint in constraints:
            csp["constraints"] = [constraint]
            for v in csp["variables"][var]:
                if not constraint_satisfied(solution, csp, var, v, solution_str=[],
                                       stdout=False):
                    if v in csp["variables"][var]:
                        csp1["variables"][var].remove(v)
                    if len(csp1["variables"][var]) == 0:
                        csp1["variables"] = csp1["variables_org"]
                        return csp1, -1
            csp["constraints"] = csp["constraints_org"]
    return csp1, 1


def constraint_satisfied(solution, csp, var, val, solution_str, stdout=True):
    constraints = [c for c in csp["constraints"]
                   for v in csp["variables"]
                   if v in c and var in c and v in solution]
    if len(constraints) == 0:
        return True
    for constraint in constraints:
        parts = constraint.split(" ")
        var1, op, var2 = parts
        if op not in ["=", ">", "<", "!"]:
            return True
        if var1 in solution:
            var1 = solution[var1]
        elif var2 in solution:
            var2 = solution[var2]
        if var1 == var:
            var1 = val
        elif var2 == var:
            var2 = val
        if ((op == "=" and var1 != var2)
                or (op == ">" and var1 <= var2)
                or (op == "<" and var1 >= var2)
                or (op == "!" and var2 == var1)):
            if stdout:
                print_stdout(solution_str + [f"{var}={val}"], "failure")
            return False
    return True


def backtrack(solution, csp):
    global STEP_CNT
    if len(solution) == len(csp["variables_org"]):
        print_stdout(solution, "solution")
        return solution
    solution_dict = {item.split("=")[0]: int(item.split("=")[1])
                     for item in solution}
    if csp["consistency"] == "fc":
        csp, ret = forward_check(csp, solution_dict)
        if ret == -1:
            print_stdout(solution, "failure")
            return -1
    var = select_variable(csp, solution_dict)
    for val in select_value(csp, var, solution_dict):
        if constraint_satisfied(solution_dict, csp, var, val, solution):
            solution.append(f"{var}={val}")
            res = backtrack(solution, csp)
            csp["constraints"] = csp["constraints_org"]
            if res != -1:
                return res
            solution.remove(f"{var}={val}")
    return -1


def csp_solver(var_file, constraint_file, consistency):
    csp = {"variables": parse_var(var_file),
           "variables_org": parse_var(var_file),
           "constraints": parse_con(constraint_file),
           "constraints_org": parse_con(constraint_file),
           "consistency": consistency}
    backtrack([], csp)


def test(file):
    with open(file, "r") as f:
        lines = [x.replace("\n", "") for x in f.readlines()]
    if len(lines) != len(OUTPUT):
        print("Lists are not equal in length.")
    else:
        unequal_elements = [(elem1, elem2) for elem1, elem2 in zip(lines, OUTPUT) if elem1 != elem2]
        if not unequal_elements:
            print("Lists are equal.")
        else:
            print("Lists are not equal.")
            print("Elements that are not equal:")
            for elem1, elem2 in unequal_elements:
                print(f"{elem1} (List 1) != {elem2} (List 2)")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("variable_file",
                        type=str,
                        help="Path to variable file")
    parser.add_argument("constraints_file",
                        type=str,
                        help="Path to constraint file")
    parser.add_argument("consistency_method", type=str,
                        help="consistency enforcing procedure: none or fc")
    args = parser.parse_args()
    csp_solver(args.variable_file, args.constraints_file, args.consistency_method)
    # test(f"./out/{args.variable_file.split('/')[-1].split('.')[0]}-{args.consistency_method}.out.txt")
