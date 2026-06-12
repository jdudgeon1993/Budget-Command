
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Foreach_comp_a163d160486f19c57684e9f111ad93ce = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.wi_grid_months_rx_state_ ?? [],((m_rx_state_,index_583f08a0050728a9b381313edf05a63e)=>(jsx("th",{css:({ ["fontSize"] : "10px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["letterSpacing"] : "0.08em", ["textTransform"] : "uppercase", ["color"] : "#BF5AF2", ["fontWeight"] : "600", ["padding"] : "8px 10px", ["textAlign"] : "right", ["minWidth"] : "100px", ["borderRight"] : "1px solid rgba(255,255,255,0.08)", ["borderBottom"] : "1px solid rgba(255,255,255,0.08)", ["whiteSpace"] : "nowrap" }),key:index_583f08a0050728a9b381313edf05a63e},m_rx_state_?.["label"]))))
    )
});
