
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_5249fd55b4121ed87e5b507d5f881e04 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{className:"prog-fill",css:({ ["height"] : "100%", ["borderRadius"] : "3px", ["background"] : ((reflex___state____state__cura___state____app_state.total_alloc_val_rx_state_ > reflex___state____state__cura___state____app_state.income_total_rx_state_) ? "#FF453A" : "#BF5AF2"), ["width"] : (reflex___state____state__cura___state____app_state.alloc_pct_rx_state_+"%") })},)
    )
});
