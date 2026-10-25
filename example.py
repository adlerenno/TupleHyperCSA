from hyperCSA import HyperCSA

dir = "0-Test/"

def main():
    hyperedgeMap = HyperCSA.calc_Map(f"{dir}hyperedge-labels")
    nodeMap = HyperCSA.calc_Map(f"{dir}node-labels")

    hyper_csa = HyperCSA(dir)
    query = [1,865,1255]

    #results = hyper_csa.query_binary_search_bounded(query)
    #results = hyper_csa.query_select_forward_bounded(query)
    #results = hyper_csa.query_select_forward_unbounded(query)
    results = hyper_csa.query_select_backward_bounded(query)
    #results = hyper_csa.query_select_backward_unbounded(query)

    for result in results:
        pass
        print(hyper_csa.decompress(result))
        print(HyperCSA.resolveName(hyperedgeMap, nodeMap, hyper_csa.decompress(result)))

if __name__ == '__main__':
    main()